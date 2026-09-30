// knit_sim: finite element simulation of a knitted membrane with cables and rods (Chapter 6, Section 6.3).
//
// The knit is an orthotropic Saint-Venant-Kirchhoff membrane whose material frame comes from the same directional
// field the knitting trajectories are extracted from, so the solver assumes the directions the machine knits. It is
// pre-strained by the stretch factors of the fabrication (Eq. 6.6), and solved together with sliding cables and
// bending-active rods held on the surface by a penalty, under a pressure load.
//
// usage: knit_sim <mesh.obj|.off> <vertex_field.txt> <params.json> <out_prefix>
//
//   mesh.obj | .off       the mesh M, in metres
//   vertex_field.txt      the wale direction per vertex, "x y z" per line in vertex order, as read by stripes
//   params.json           {
//                           "E_wale": 10300, "E_course": 13400, "nu": 0.58,   membrane moduli (N/m) and Poisson ratio
//                           "thickness": 1.0, "mass": 0.001,                   (optional)
//                           "pressure": 1000,                                  Pa
//                           "stretch_wale": 1.0, "stretch_course": 1.0,        a number, or one per face
//                           "fixed_vertices": [...],                           (optional; default the whole boundary)
//                           "cables": [{"path": [v, ...], "EA": 157000, "rest_scale": 1.0}, ...],
//                           "rods": [{"path": [v, ...], "E": 2e11, "thickness": 0.003, "width": 0.003}, ...],
//                           "contact_stiffness": 1e5,                          rod-surface penalty (N/m)
//                           "load_steps": 0                                    0: 1, 10, 50, 100 % of the pressure
//                         }
//
// outputs:
//   <prefix>_deformed.obj   the deformed membrane
//   <prefix>_rods.obj       the deformed rods, as polylines, if any
//   <prefix>_stress.csv     the stress per face
//   <prefix>_summary.json   solver status and residual, crown height, stresses, cable tensions

#include <fsim/CompositeModel.h>
#include <fsim/OrthotropicStVKMembrane.h>
#include <fsim/RodCollection.h>
#include <fsim/util/io.h>
#include <optim/NewtonSolver.h>

#include "anisotropic_rest_shape.h"
#include "rod_surface_contact.h"
#include "sliding_cable.h"
#include "stress_analysis.h"

#include <nlohmann/json.hpp>

#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>

using namespace Eigen;
using json = nlohmann::json;

namespace
{
// any number of sliding cables, as one model
struct Cables
{
  std::vector<SlidingCable> cables;

  double energy(const Ref<const VectorXd>& X) const
  {
    double e = 0;
    for(auto& c: cables)
      e += c.energy(X);
    return e;
  }
  void gradient(const Ref<const VectorXd>& X, Ref<VectorXd> Y) const
  {
    for(auto& c: cables)
      c.gradient(X, Y);
  }
  VectorXd gradient(const Ref<const VectorXd>& X) const
  {
    VectorXd Y = VectorXd::Zero(X.size());
    gradient(X, Y);
    return Y;
  }
  std::vector<Triplet<double>> hessianTriplets(const Ref<const VectorXd>& X) const
  {
    std::vector<Triplet<double>> t;
    for(auto& c: cables)
    {
      auto ct = c.hessianTriplets(X);
      t.insert(t.end(), ct.begin(), ct.end());
    }
    return t;
  }
  SparseMatrix<double> hessian(const Ref<const VectorXd>& X) const
  {
    auto t = hessianTriplets(X);
    SparseMatrix<double> H(X.size(), X.size());
    H.setFromTriplets(t.begin(), t.end());
    return H;
  }
};

void readMesh(const std::string& path, fsim::Mat3<double>& V, fsim::Mat3<int>& F)
{
  if(path.size() > 4 && path.substr(path.size() - 4) == ".off")
  {
    fsim::readOFF(path, V, F);
    return;
  }
  // .obj, in the order of the file, as stripes reads it
  std::vector<Vector3d> v;
  std::vector<Vector3i> f;
  std::ifstream in(path);
  if(!in)
    throw std::runtime_error("cannot read the mesh " + path);
  std::string line;
  while(std::getline(in, line))
  {
    std::istringstream s(line);
    std::string tag;
    s >> tag;
    if(tag == "v")
    {
      Vector3d p;
      s >> p.x() >> p.y() >> p.z();
      v.push_back(p);
    }
    else if(tag == "f")
    {
      Vector3i t;
      for(int k = 0; k < 3; ++k)
      {
        std::string token;
        s >> token;
        t[k] = std::stoi(token.substr(0, token.find('/'))) - 1;
      }
      f.push_back(t);
    }
  }
  V.resize(v.size(), 3);
  F.resize(f.size(), 3);
  for(size_t i = 0; i < v.size(); ++i)
    V.row(i) = v[i];
  for(size_t i = 0; i < f.size(); ++i)
    F.row(i) = f[i];
}

std::vector<Vector3d> readField(const std::string& path)
{
  std::vector<Vector3d> field;
  std::ifstream in(path);
  if(!in)
    throw std::runtime_error("cannot read the field " + path);
  std::string line;
  while(std::getline(in, line))
  {
    std::istringstream s(line);
    Vector3d u;
    if(s >> u.x() >> u.y() >> u.z())
      field.push_back(u);
  }
  return field;
}

// the wale direction in each face: the corner vectors flipped to agree with the first (a line field), averaged, and
// projected into the face, as stripes does
std::vector<Vector3d> faceWale(const fsim::Mat3<double>& V, const fsim::Mat3<int>& F,
                               const std::vector<Vector3d>& field)
{
  std::vector<Vector3d> wale(F.rows());
  for(int f = 0; f < F.rows(); ++f)
  {
    Vector3d first = field[F(f, 0)], sum = first;
    for(int k = 1; k < 3; ++k)
    {
      Vector3d u = field[F(f, k)];
      sum += u.dot(first) < 0 ? Vector3d(-u) : u;
    }
    Vector3d n = (V.row(F(f, 1)) - V.row(F(f, 0))).cross(V.row(F(f, 2)) - V.row(F(f, 0))).normalized();
    Vector3d p = sum - sum.dot(n) * n;
    wale[f] = p.norm() > 1e-12 ? p.normalized() : Vector3d(V.row(F(f, 1)) - V.row(F(f, 0))).normalized();
  }
  return wale;
}

std::vector<int> boundaryVertices(const fsim::Mat3<int>& F)
{
  std::map<std::pair<int, int>, int> count;
  for(int f = 0; f < F.rows(); ++f)
    for(int k = 0; k < 3; ++k)
    {
      int a = F(f, k), b = F(f, (k + 1) % 3);
      ++count[std::minmax(a, b)];
    }
  std::set<int> boundary;
  for(auto& [e, c]: count)
    if(c == 1)
      boundary.insert({e.first, e.second});
  return {boundary.begin(), boundary.end()};
}

// a number, or one per face
std::vector<double> perFace(const json& p, const std::string& key, int nF, double fallback)
{
  if(!p.contains(key))
    return std::vector<double>(nF, fallback);
  if(p[key].is_number())
    return std::vector<double>(nF, p[key].get<double>());
  auto v = p[key].get<std::vector<double>>();
  if((int)v.size() != nF)
    throw std::runtime_error(key + " has " + std::to_string(v.size()) + " values, the mesh " + std::to_string(nF) +
                             " faces");
  return v;
}

struct Status
{
  std::string status = "unrun";
  double residual = 0;
};

template <class Model, class Update>
VectorXd newton(Model& model, const VectorXd& x0, const std::vector<int>& fixed, double regMax, Update update,
                Status& result)
{
  optim::NewtonSolver<double> solver;
  solver.options.display = optim::SolverDisplay::quiet;
  solver.options.threshold = 1e-6;
  solver.options.iteration_limit = 10000;
  // the line search of the thesis runs, more permissive than optim's default
  solver.options.line_search.c1 = 1e-6;
  solver.options.line_search.c2 = 0.99;
  if(regMax > 0)
    solver.options.newton.max = regMax;
  for(int v: fixed)
    for(int k = 0; k < 3; ++k)
      solver.options.fixed_dofs.push_back(3 * v + k);
  solver.options.update_fct = update;
  solver.solve(model, x0);

  switch(solver.info())
  {
    case optim::SolverStatus::success: result.status = "success"; break;
    case optim::SolverStatus::line_search_failed: result.status = "line_search_failed"; break;
    case optim::SolverStatus::wrong_descent_direction: result.status = "wrong_descent_direction"; break;
    case optim::SolverStatus::regularization_failed: result.status = "regularization_failed"; break;
    case optim::SolverStatus::iteration_overflow: result.status = "iteration_overflow"; break;
    case optim::SolverStatus::NaN_error: result.status = "NaN_error"; break;
    default: result.status = "unknown";
  }
  // the force left on the free degrees of freedom, which tells a flat energy apart from a solve still far off
  VectorXd g = model.gradient(solver.var());
  for(int v: fixed)
    g.segment<3>(3 * v).setZero();
  result.residual = g.cwiseAbs().maxCoeff();
  return solver.var();
}
} // namespace

int main(int argc, char* argv[])
{
  if(argc < 5)
  {
    std::cerr << "usage: knit_sim <mesh.obj|.off> <vertex_field.txt> <params.json> <out_prefix>\n";
    return 1;
  }
  const std::string prefix = argv[4];

  try
  {
    fsim::Mat3<double> V0;
    fsim::Mat3<int> F;
    readMesh(argv[1], V0, F);
    const int nV = V0.rows(), nF = F.rows();
    auto field = readField(argv[2]);
    if((int)field.size() != nV)
      throw std::runtime_error("the field has " + std::to_string(field.size()) + " vectors, the mesh " +
                               std::to_string(nV) + " vertices");
    std::ifstream pf(argv[3]);
    if(!pf)
      throw std::runtime_error(std::string("cannot read the parameters ") + argv[3]);
    json p = json::parse(pf);

    // the material, stated explicitly: there is no default
    for(auto key: {"E_wale", "E_course", "nu", "pressure"})
      if(!p.contains(key))
        throw std::runtime_error(std::string("params.json needs ") + key);
    const double pressure = p["pressure"];
    const double mass = p.value("mass", 0.001);
    std::vector<double> Ew(nF, p["E_wale"].get<double>()), Ec(nF, p["E_course"].get<double>()),
        nu(nF, p["nu"].get<double>()), thickness(nF, p.value("thickness", 1.0));

    // the material frame, from the field; the pre-strained rest shape, the stitches scaled by 1 / stretch (Eq. 6.6)
    std::vector<Vector3d> wale = faceWale(V0, F, field);
    std::vector<int> boundary = boundaryVertices(F);
    auto sw = perFace(p, "stretch_wale", nF, 1.0), sc = perFace(p, "stretch_course", nF, 1.0);
    std::vector<double> s1(nF), s2(nF);
    for(int f = 0; f < nF; ++f)
    {
      s1[f] = 1.0 / sw[f];
      s2[f] = 1.0 / sc[f];
    }
    fsim::Mat3<double> rest = computeAnisotropicRestShape(V0, F, boundary, wale, s1, s2);

    std::vector<int> fixed = p.value("fixed_vertices", boundary);
    for(int v: fixed)
      if(v < 0 || v >= nV)
        throw std::runtime_error("fixed_vertices has an index out of range: " + std::to_string(v));

    // cables: sliding, with a uniform tension over their whole length
    Cables cables;
    for(auto& c: p.value("cables", json::array()))
    {
      std::vector<int> path = c["path"];
      for(int v: path)
        if(v < 0 || v >= nV)
          throw std::runtime_error("a cable path has an index out of range: " + std::to_string(v));
      double length = 0;
      for(size_t k = 0; k + 1 < path.size(); ++k)
        length += (V0.row(path[k + 1]) - V0.row(path[k])).norm();
      cables.cables.emplace_back(path, c.value("EA", 157000.0), c.value("rest_scale", 1.0) * length);
    }

    // rods: their own nodes after the membrane vertices, held on the surface by a penalty
    std::vector<std::vector<int>> rodPaths, rodNodes;
    std::vector<double> rodThickness, rodWidth;
    double rodE = 0;
    for(auto& r: p.value("rods", json::array()))
    {
      rodPaths.push_back(r["path"].get<std::vector<int>>());
      rodThickness.push_back(r.value("thickness", 0.003));
      rodWidth.push_back(r.value("width", 0.003));
      double E = r.value("E", 2e11);
      if(rodE && E != rodE)
        throw std::runtime_error("all rods need the same E");
      rodE = E;
    }
    int nRod = 0;
    for(auto& path: rodPaths)
    {
      std::vector<int> nodes;
      for(int v: path)
      {
        if(v < 0 || v >= nV)
          throw std::runtime_error("a rod path has an index out of range: " + std::to_string(v));
        nodes.push_back(nV + nRod++);
      }
      rodNodes.push_back(nodes);
    }
    fsim::Mat3<double> Vext(nV + nRod, 3);
    Vext.topRows(nV) = V0;
    for(size_t r = 0, k = 0; r < rodPaths.size(); ++r)
      for(int v: rodPaths[r])
        Vext.row(nV + k++) = V0.row(v);

    std::cerr << "mesh " << nV << " vertices " << nF << " faces, " << boundary.size() << " on the boundary, "
              << fixed.size() << " fixed, " << cables.cables.size() << " cables, " << rodPaths.size() << " rods ("
              << nRod << " nodes)\n";

    std::vector<double> steps = {0.01 * pressure, 0.1 * pressure, 0.5 * pressure, pressure};
    int nSteps = p.value("load_steps", 0);
    if(nSteps >= 2)
    {
      steps.clear();
      for(int k = 0; k < nSteps; ++k)
        steps.push_back(pressure * std::pow(0.01, 1.0 - double(k) / (nSteps - 1)));
    }
    const double regMax = p.value("newton_reg_max", 0.0);
    const double kContact = p.value("contact_stiffness", 1e5);

    Status status;
    VectorXd x;
    VectorXd rodX; // the rod nodes and twists, when there are rods
    if(rodPaths.empty())
    {
      x = Map<const VectorXd>(V0.data(), 3 * nV);
      for(double load: steps)
      {
        fsim::OrthotropicStVKMembrane membrane(rest, F, thickness, Ew, Ec, nu, wale, mass, load);
        fsim::CompositeModel model(std::move(membrane), Cables(cables));
        x = newton(model, x, fixed, regMax, [](const Ref<const VectorXd>) {}, status);
        std::cerr << "pressure " << load << ": " << status.status << ", residual " << status.residual << "\n";
      }
    }
    else
    {
      fsim::Mat3<double> N(rodPaths.size(), 3);
      for(size_t r = 0; r < rodPaths.size(); ++r)
      {
        Vector3d e0 = (V0.row(rodPaths[r][1]) - V0.row(rodPaths[r][0])).normalized();
        N.row(r) = e0.unitOrthogonal();
      }
      fsim::Mat2<int> C(0, 2);
      fsim::RodCollection probe(Vext, rodNodes, C, N, rodThickness, rodWidth, rodE);
      x = VectorXd::Zero(3 * (nV + nRod) + probe.nbEdges());
      x.head(3 * (nV + nRod)) = Map<const VectorXd>(Vext.data(), 3 * (nV + nRod));
      for(double load: steps)
      {
        fsim::OrthotropicStVKMembrane membrane(rest, F, thickness, Ew, Ec, nu, wale, mass, load);
        fsim::RodCollection rods(Vext, rodNodes, C, N, rodThickness, rodWidth, rodE);
        RodSurfaceContact contact(nV, nRod, kContact, F, x);
        fsim::CompositeModel model(std::move(membrane), Cables(cables), std::move(rods), std::move(contact));
        auto update = [&model](const Ref<const VectorXd> X) {
          model.getModel<2>().updateProperties(X);
          model.getModel<3>().updateContacts(X);
        };
        x = newton(model, x, fixed, regMax, update, status);
        std::cerr << "pressure " << load << ": " << status.status << ", residual " << status.residual << "\n";
      }
    }

    // outputs
    fsim::Mat3<double> V = Map<const fsim::Mat3<double>>(x.data(), nV, 3);
    {
      std::ofstream out(prefix + "_deformed.obj");
      out << std::setprecision(10);
      for(int i = 0; i < nV; ++i)
        out << "v " << V(i, 0) << " " << V(i, 1) << " " << V(i, 2) << "\n";
      for(int f = 0; f < nF; ++f)
        out << "f " << F(f, 0) + 1 << " " << F(f, 1) + 1 << " " << F(f, 2) + 1 << "\n";
    }
    if(nRod)
    {
      std::ofstream out(prefix + "_rods.obj");
      out << std::setprecision(10);
      for(int k = 0; k < nRod; ++k)
        out << "v " << x(3 * (nV + k)) << " " << x(3 * (nV + k) + 1) << " " << x(3 * (nV + k) + 2) << "\n";
      int k = 0;
      for(auto& path: rodPaths)
      {
        out << "l";
        for(size_t i = 0; i < path.size(); ++i)
          out << " " << ++k;
        out << "\n";
      }
    }
    fsim::OrthotropicStVKMembrane membrane(rest, F, thickness, Ew, Ec, nu, wale, mass, pressure);
    auto stress = computeElementStresses(membrane, x.head(3 * nV), 0, 0, 0, 0);
    saveStressCSV(prefix + "_stress.csv", stress);

    double crown = -std::numeric_limits<double>::infinity(), maxStress = 0, meanStress = 0;
    std::set<int> onBoundary(boundary.begin(), boundary.end());
    for(int i = 0; i < nV; ++i)
      if(!onBoundary.count(i))
        crown = std::max(crown, V(i, 2));
    for(auto& s: stress)
    {
      maxStress = std::max(maxStress, s.von_mises);
      meanStress += s.von_mises / stress.size();
    }
    json tensions = json::array();
    for(auto& c: cables.cables)
    {
      double L = 0;
      for(size_t k = 0; k + 1 < c.indices.size(); ++k)
        L += (V.row(c.indices[k + 1]) - V.row(c.indices[k])).norm();
      tensions.push_back(std::max(0.0, c.EA / c.L_rest * (L - c.L_rest)));
    }
    json summary = {{"status", status.status},         {"residual", status.residual},
                    {"crown_height", crown},           {"max_stress", maxStress},
                    {"mean_stress", meanStress},       {"cable_tensions", tensions},
                    {"vertices", nV},                  {"faces", nF},
                    {"cables", cables.cables.size()}, {"rods", rodPaths.size()}};
    std::ofstream(prefix + "_summary.json") << summary.dump(2) << "\n";
    std::cerr << "status " << status.status << ", crown " << crown << "\n";
    return status.status == "success" ? 0 : 2;
  }
  catch(const std::exception& e)
  {
    std::cerr << "error: " << e.what() << "\n";
    return 1;
  }
}
