#include <iostream>
#include <igl/opengl/glfw/Viewer.h>
#include <igl/read_triangle_mesh.h>
#include <igl/heat_geodesics.h>
#include <igl/avg_edge_length.h>
#include "isolines_colormap.h"
#include "update.h"
#include <igl/material_colors.h>
#include <igl/isolines.h>

/*
void set_colormap(igl::opengl::glfw::Viewer & viewer)
{
  const int num_intervals = 30;
  Eigen::MatrixXd CM(num_intervals,3);
  // Colormap texture
  for(int i = 0;i<num_intervals;i++)
  {
    double t = double(num_intervals - i - 1)/double(num_intervals-1);
    CM(i,0) = std::max(std::min(2.0*t-0.0,1.0),0.0);
    CM(i,1) = std::max(std::min(2.0*t-1.0,1.0),0.0);
    CM(i,2) = std::max(std::min(6.0*t-5.0,1.0),0.0);
  }
  igl::isolines_map(Eigen::MatrixXd(CM),CM);
  viewer.data().set_colormap(CM);
}
*/

int main(int argc, char *argv[])
{
  Eigen::MatrixXd V;
  Eigen::MatrixXi F;

  // const std::string obj_path = "/Users/duch/documents/github/libigl-tutorial-data/data/snail.obj";
  const std::string obj_path = "/Users/duch/Documents/PhD/knit/benchmarks/semisphere.obj";
  igl::read_triangle_mesh(obj_path, V, F);
  double t = std::pow(igl::avg_edge_length(V, F), 2); // time step, good result is half average length

  // Precomputation
  igl::HeatGeodesicsData<double> data;
  const auto precompute = [&]()
  {
    if (!igl::heat_geodesics_precompute(V, F, t, data))
    {
      std::cerr << "Error: heat_geodesics_precompute failed." << std::endl;
      exit(EXIT_FAILURE);
    };
  };
  precompute();

  // solve heat distance
  Eigen::VectorXd D;
  Eigen::VectorXi gamma(7);
  gamma << 0, 2, 5, 12, 25, 33, 839;
  igl::heat_geodesics_solve(data, gamma, D);

  // isolines
  const int n = argc > 2 ? atoi(argv[2]) : 128;

  float maxdis = D.maxCoeff();
  float target_dis = 3;  // distance between the lines
  double result = maxdis / target_dis;
  int num = static_cast<int>(result);

  Eigen::VectorXd vals = Eigen::VectorXd::LinSpaced(num + 2, 0, D.maxCoeff());
  Eigen::MatrixXd iV;
  Eigen::MatrixXi iE;
  Eigen::VectorXi I;

  igl::isolines(V, F, D, vals, iV, iE, I);

  std::cout << V << F << iV << std::endl;
  
  
  {
    // Open a file for writing
    // std::ofstream file("/Users/duch/documents/github/compas_knit/src/cpp_libigl/build/temp/output.txt");
    std::ofstream file("/Users/duch/Documents/PhD/knit/benchmarks/semisphere_output.txt");

    // Redirect std::cout to the file
    std::streambuf* original_cout = std::cout.rdbuf();
    std::cout.rdbuf(file.rdbuf());

    // Now, anything written to std::cout will be saved in the file
    std::cout << iV << std::endl;
    std::cout << std::endl;
    std::cout << iE << std::endl;
    std::cout << std::endl;
    std::cout << I << std::endl;

    // Restore the original std::cout buffer
    std::cout.rdbuf(original_cout);

    // Close the file
    file.close();
  }

  // init the viewer
  igl::opengl::glfw::Viewer viewer;

  // Plot the mesh

  viewer.data().set_mesh(V, F);
  viewer.data().label_size = 10;
  viewer.data().add_label(viewer.data().V.row(0) + viewer.data().V_normals.row(0).normalized() * 0.005, "Hello World!");

  viewer.data().set_face_based(true);
  viewer.data().show_faces = true;
  viewer.data().show_lines = false;
  viewer.data().uniform_colors(
      Eigen::Vector3d(0.94 * viewer.core().background_color.head<3>().cast<double>()),
      Eigen::Vector3d(0.05 * viewer.core().background_color.head<3>().cast<double>()),
      Eigen::Vector3d(0.01 * viewer.core().background_color.head<3>().cast<double>()));

  viewer.core().lighting_factor = 0.5;
  viewer.data().set_edges(iV, iE,
                          Eigen::RowVector3d(igl::GOLD_DIFFUSE[0], igl::GOLD_DIFFUSE[1], igl::GOLD_DIFFUSE[2]));
  viewer.data().line_width = 1;

  viewer.launch();
}