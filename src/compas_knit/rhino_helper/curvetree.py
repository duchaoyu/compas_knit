import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
from clr import AddReference as addr
addr("Grasshopper")
from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

class  pt_class:
    def __init__(self,pt,index,num,edge,neighbor,end):
        self.pt = pt
        self.index = index
        self.num = num
        self.edge = edge #0 stand for true, -1 stands for false
        self.neighbor = neighbor
        self.end = end #0 stand for true, -1 stands for false

class simple_pt_class:
    def __init__(self,pt,index,num):
        self.pt = pt
        self.index = index
        self.num = num

class sort_pt_class:
    def __init__(self,pt,center_pt,index,num,color,mo_color,top,top_next,next):
        self.pt = pt
        self.index = index
        self.num = num
        self.color = color
        self.center_pt = center_pt
        self.mo_color = mo_color
        self.top = top
        self.top_next = top_next
        self.next = next

class weft_line_class:
    def __init__(self,weft_line,index,num,st_pt,end_pt,end_pt_index,counted_bool):
        self.weft_line = weft_line
        self.st_pt = st_pt
        self.end_pt = end_pt
        self.index = index
        self.num = num    
        self.end_pt_index = end_pt_index
        self.counted_bool = counted_bool

class weft_class:
    def __init__(self,weft,index,num,st_pt,end_pt):
        self.weft = weft
        self.index = index
        self.num = num        
        self.st_pt = st_pt
        self.end_pt = end_pt

class warp_class:
    def __init__(self,weft,num):
        self.weft = weft
        self.num = num

def dataTreeToList(aTree):
    theList = []
    for i in range(aTree.BranchCount ):
        thisListPart = []
        thisBranch = aTree.Branch(i)
        for j in range(len(thisBranch)):
            thisListPart.append( thisBranch[j] )
        theList.append(thisListPart)
    return theList

def raggedListToDataTree(raggedList):
    rl = raggedList
    result = DataTree[object]()
    for i in range(len(rl)):
        temp = []
        for j in range(len(rl[i])):
            temp.append(rl[i][j])
        #print i, " - ",temp
        path = GH_Path(i)
        result.AddRange(temp, path)
    return result

def seg_num(curve,dist):
    segnum = rs.CurveLength(curve)//dist
    if segnum ==0:
        segnum=1
    if (rs.CurveLength(curve)/segnum) < dist-1.5 and segnum>1:
        segnum = segnum - 1
    if (rs.CurveLength(curve)/segnum) > dist+1.5:
        segnum = segnum + 1
    return int(segnum)

def min_distance_point_index(pt_origin,ptslist_target):
    temp_pts_list = []
    temp_pts_list[:] = [e.pt for e in ptslist_target]
    closest_pt = rs.PointClosestObject(pt_origin.pt,temp_pts_list)[0]
    pt_index = [] 
    pt_index[:] = [i for i in range(0,len(ptslist_target)) if ptslist_target[i].pt==closest_pt]
    return pt_index[0]

def list_min_distance_point_index(pt_origin,ptslist_target):
    temp_pts_list = []
    list_item = []
    list_index = []
    index01 = []
    index02 = []
    index03 = []
    temp_pts_list[:] = [e for e in ptslist_target if e.pt<>pt_origin.pt] #exclude overlapped points
    temp_pts_list.sort(key=lambda x:rs.Distance(x.pt,pt_origin.pt),reverse=False)
    item01 = temp_pts_list[0]
    item02 = temp_pts_list[1]
    item03 = temp_pts_list[2]
    list_item[:] = [item01,item02]
    index01[:] = [i for i in range (0,len(ptslist_target)) if ptslist_target[i].pt==item01.pt]
    index02[:] = [i for i in range (0,len(ptslist_target)) if ptslist_target[i].pt==item02.pt]
    index03[:] = [i for i in range (0,len(ptslist_target)) if ptslist_target[i].pt==item03.pt]
    list_index[:] =[index01[0],index02[0],index03[0]] 
    min_least_dist = rs.Distance(item01.pt,pt_origin.pt)
    return list_index,min_least_dist

def most_vertical(pts_index_to_comp,ref_vector,object_pt,target_ptslist):
    list_angle =[]
    vector01 = rs.VectorCreate(target_ptslist[pts_index_to_comp[0]].pt,object_pt.pt)
    vector02 = rs.VectorCreate(target_ptslist[pts_index_to_comp[1]].pt,object_pt.pt)
    vector03 = rs.VectorCreate(target_ptslist[pts_index_to_comp[2]].pt,object_pt.pt)
    angle01 = abs(rs.VectorAngle(vector01,ref_vector)-90)
    angle02 = abs(rs.VectorAngle(vector02,ref_vector)-90)
    angle03 = abs(rs.VectorAngle(vector03,ref_vector)-90)
    list_angle[:]=[angle01,angle02,angle03]
    angle_ref = 90
    num = -1
    for i in range (0,len(list_angle)):
        if list_angle[i] < angle_ref:
            angle_ref = list_angle[i]
            num = pts_index_to_comp[i]
    return num

def next_pt_index(cur_pt,cur_list,next_list):
    pt_index_list = []
    cur_pts_index = []
    if cur_pt.edge <> 0:#find the most vertical among 4 closest points  
        pt_index_list[:],min_dist = list_min_distance_point_index(cur_pt,next_list)
        cur_pts_index[:],cur_min_dist = list_min_distance_point_index(cur_pt,cur_list)
        closest_pt = next_list[min_distance_point_index(cur_pt,next_list)]
        closest_distance = rs.Distance(closest_pt.pt,cur_pt.pt)
        if  closest_distance < 1e-8:
            pt_index = min_distance_point_index(cur_pt,next_list)
        if closest_distance >1e-8:
            vector01 = rs.VectorUnitize(rs.VectorCreate(cur_list[cur_pts_index[0]].pt,cur_pt.pt))
            vector02 = rs.VectorUnitize(rs.VectorCreate(cur_list[cur_pts_index[1]].pt,cur_pt.pt))
            vector_ref = rs.VectorAdd(vector01,rs.VectorReverse(vector02))
            pt_index = most_vertical(pt_index_list,vector_ref,cur_pt,next_list)
    else:
        pt_index= min_distance_point_index(cur_pt,next_list)
    return pt_index

def find_index_from_list(target_list,origin_point,origin_point_num):
    list_index = []
    index= -1
    list_index[:] = [i for i in range(0,len(target_list))if target_list[i].pt==origin_point and origin_point_num == target_list[i].num-1] #last warp should be in the same row
    if len(list_index)>0 : 
        index = list_index[0]
    return index

def wefts_list_to_next(ptslist_origin,ptslist_target,globalptslist01,globalptslist02,width,height,list_crvs):
    temp_weftslist = []
    indexlist01_a = []
    indexlist01_b = []
    indexlist02 = []
    for i in range (len(ptslist_origin)):
        cur_pts = []
        next_pts = []
        next_pts[:] = []
        num_neighbor_a = []
        num_neighbor_b = []
        test_pts = []
        test_pts[:] = [e.pt for e in ptslist_target]
        if i == len(ptslist_origin)-1:
            temp_test_pts= []
            temp_test_pts[:] = [e.pt for e in ptslist_target if e.index<>0 and e.index<>1  ]
        if i < len(ptslist_origin)-1:
            temp_test_pts= []
            temp_test_pts[:] = [e.pt for e in ptslist_target]
        temp_pts=[]
        temp_pts[:] = ptslist_target
        ###next_pts###
        closest_pt = rs.PointClosestObject(ptslist_origin[i].pt,temp_test_pts)[0]
        temp_test_list = []
        temp_test_list[:] = [k for k in range(0,len(test_pts)) if test_pts[k] == closest_pt]
        ref_index = temp_test_list[0]
        for j in range(ref_index-5,ref_index+5):
            if j>=0 and j<len(test_pts):
                next_pts.append(temp_pts[j])
        ###cur_pts###
        if  ptslist_origin[i].edge <>0:
            if ptslist_origin[i].index==len(globalptslist01)-2:
                cur_pts[:] = [globalptslist01[ptslist_origin[i].index-2],globalptslist01[ptslist_origin[i].index-1],globalptslist01[ptslist_origin[i].index+1]]
            if  ptslist_origin[i].index < len(globalptslist01)-2:
                cur_pts[:] = [globalptslist01[ptslist_origin[i].index-1],globalptslist01[ptslist_origin[i].index+1],globalptslist01[ptslist_origin[i].index+2]]
        ###in_pts###
        if len(next_pts) <> 0 and  ptslist_origin[i].edge<>0:
            pt_index = next_pt_index(ptslist_origin[i],cur_pts,next_pts)
            line = rs.AddLine(ptslist_origin[i].pt,next_pts[pt_index].pt)
            long_crv01 = list_crvs[ptslist_origin[i].num]
            long_crv = list_crvs[temp_pts[0].num]
            cur_pts.sort(key=lambda x:rs.CurveClosestPoint(long_crv01,x.pt),reverse=False)
            next_pts.sort(key=lambda x:rs.CurveClosestPoint(long_crv,x.pt),reverse=False)
            if rs.Distance(ptslist_origin[i].pt,next_pts[pt_index].pt) < max(width,height)*2:
                if len(temp_weftslist) < 1: #avoid intersection
                    the_end_pt = next_pts[pt_index].pt
                    line = rs.AddLine(ptslist_origin[i].pt,next_pts[pt_index].pt)
                    end_pt_index =  next_pts[pt_index].index
                else: #avoid intersection
                    prev_pt_index= find_index_from_list(next_pts,temp_weftslist[-1].end_pt,temp_weftslist[-1].num) # in case of X(intersection) situcation
                    if prev_pt_index<>-1: #last warp should be in the same row
                        if  next_pts[pt_index].index < next_pts[prev_pt_index].index and next_pts[prev_pt_index].index-next_pts[pt_index].index<len(next_pts)/2:
                            the_end_pt = next_pts[prev_pt_index].pt
                            line = rs.AddLine(ptslist_origin[i].pt,next_pts[prev_pt_index].pt)
                            end_pt_index =  next_pts[prev_pt_index].index
                        else:
                            the_end_pt = next_pts[pt_index].pt
                            line = rs.AddLine(ptslist_origin[i].pt,next_pts[pt_index].pt)
                            end_pt_index = next_pts[pt_index].index
                    else:    
                        #the_end_pt = next_pts[pt_index].pt
                        line = rs.AddLine(ptslist_origin[i].pt,next_pts[pt_index].pt)
                        end_pt_index = next_pts[pt_index].index
                if rs.Distance(ptslist_origin[i].pt,the_end_pt) < max(width,height)*2:
                    temp_weftslist.append(weft_line_class(line,ptslist_origin[i].index,ptslist_origin[i].num,ptslist_origin[i].pt,the_end_pt,end_pt_index,False))
                    num_neighbor_a[:] = [k for k in range (0,len(globalptslist01)) if globalptslist01[k].pt==ptslist_origin[i].pt ]
                    num_neighbor_b[:] = [k for k in range (0,len(globalptslist02)) if globalptslist02[k].pt==the_end_pt] 
                    # add number of neighbor
                    if len(num_neighbor_a) <> 0:
                        indexlist01_a.extend(num_neighbor_a)
                    if len(num_neighbor_b) <> 0:
                        indexlist01_b.extend(num_neighbor_b)
                if rs.Distance(ptslist_origin[i].pt,the_end_pt) >= max(width,height)*2:
                    for k in range (0,len(globalptslist01)): # add end property
                        if globalptslist01[k].pt == ptslist_origin[i].pt:
                            indexlist02.append(k)
            if rs.Distance(ptslist_origin[i].pt,next_pts[pt_index].pt) >= max(width,height)*2:
                for k in range (0,len(globalptslist01)): # add end property
                    if globalptslist01[k].pt == ptslist_origin[i].pt:
                         indexlist02.append(k)
        ###edge_pts###
        if len(next_pts) <> 0 and  ptslist_origin[i].edge==0:# for edge pts
            pt_index = min_distance_point_index(ptslist_origin[i],next_pts)
            test_dist = rs.Distance(ptslist_origin[i].pt,next_pts[pt_index].pt)
            the_end_pt = next_pts[pt_index].pt
            line = rs.AddLine(ptslist_origin[i].pt,next_pts[pt_index].pt)
            end_pt_index =  next_pts[pt_index].index
            if (next_pts[pt_index].index==len(globalptslist02)-1 and ptslist_origin[i].index==0) or (next_pts[pt_index].index==0 and ptslist_origin[i].index==len(globalptslist01)-1):
                new_next_pts= []
                new_next_pts[:] = next_pts
                del(new_next_pts[pt_index])
                new_pt_index =  min_distance_point_index(ptslist_origin[i],new_next_pts)
                test_dist = rs.Distance(ptslist_origin[i].pt,new_next_pts[new_pt_index].pt)
                the_end_pt = new_next_pts[new_pt_index].pt
                line = rs.AddLine(ptslist_origin[i].pt,new_next_pts[new_pt_index].pt)
                end_pt_index =  new_next_pts[new_pt_index].index
            if test_dist < max(width,height)*2:
                temp_weftslist.append(weft_line_class(line,ptslist_origin[i].index,ptslist_origin[i].num,ptslist_origin[i].pt,the_end_pt,end_pt_index,False))
                num_neighbor_a[:] = [k for k in range (0,len(globalptslist01)) if globalptslist01[k].pt==ptslist_origin[i].pt] # add number of neighbor
                num_neighbor_b[:] = [k for k in range (0,len(globalptslist02)) if globalptslist02[k].pt==the_end_pt] 
                if len(num_neighbor_a) <> 0:
                    indexlist01_a.extend(num_neighbor_a)
                if len(num_neighbor_b) <> 0:
                    indexlist01_b.extend(num_neighbor_b)
            if test_dist >= max(width,height)*2:
                for k in range (0,len(globalptslist01)): # add end 
                    if globalptslist01[k].pt == ptslist_origin[i].pt:
                         indexlist02.append(k)
    return temp_weftslist,indexlist01_a,indexlist01_b,indexlist02

# attention when is closed surface
def avoid_intersection_index(original_pt,pt_next_index,the_prev_pts,the_cur_pts,the_ref_lines): 
    prev_end_pt = []
    next_end_pt =[]
    prev_lines = []
    prev_line =[]
    inter_line = []
    st_point = the_prev_pts[pt_next_index]
    line = rs.AddLine(the_prev_pts[pt_next_index].pt,original_pt.pt)#prev point should be st point
    index = the_prev_pts[pt_next_index].index
    num =  the_prev_pts[pt_next_index].num
    prev_lines[:] = [e for e in the_ref_lines if e.num == the_prev_pts[pt_next_index].num and e.num == original_pt.num-1 ]
    prev_line[:] = [e for e in prev_lines if (e.index > the_prev_pts[pt_next_index].index and e.end_pt_index < original_pt.index and e.index - the_prev_pts[pt_next_index].index<len(the_prev_pts)/2 and original_pt.index - e.end_pt_index < len(the_prev_pts)/2) or (e.index < the_prev_pts[pt_next_index].index and e.end_pt_index> original_pt.index and the_prev_pts[pt_next_index].index - e.index <len(the_prev_pts)/2 and  e.end_pt_index - original_pt.index <len(the_prev_pts)/2 ) ]
    if len(prev_line) >0:
        prev_line.sort(key=lambda x:abs(x.index - the_prev_pts[pt_next_index].index), reverse = False) 
        st_point = prev_line[0].st_pt
        line = rs.AddLine(prev_line[0].st_pt,original_pt.pt,) #prev point should be st point
        index = prev_line[0].index
        num = prev_line[0].num
        return line,index,num,st_point
    else:
        st_point = the_prev_pts[pt_next_index].pt
        line = rs.AddLine(the_prev_pts[pt_next_index].pt,original_pt.pt) #prev point should be st point
        index = the_prev_pts[pt_next_index].index
        num =  the_prev_pts[pt_next_index].num
        return line,index,num,st_point

def wefts_list_to_prev(ptslist_origin,ptslist_target,globalptslist01,globalptslist02,width,height,prev_lines):
    temp_weftslist = []
    indexlist01_a = []
    indexlist01_b = []
    indexlist02 = []
    ref_lines = []
    ref_lines[:] = prev_lines
    for i in range (len(ptslist_origin)):
        prev_pts = []
        cur_pts = []
        num_neighbor_a = []
        num_neighbor_b = []

        test_pts = []
        test_pts[:] = [e.pt for e in ptslist_target]
        ###prev_pts###
        closest_pt = rs.PointClosestObject(ptslist_origin[i].pt,test_pts)[0]
        temp_test_list = []
        temp_test_list[:] = [k for k in range(0,len(test_pts)) if test_pts[k] == closest_pt]
        ref_index = temp_test_list[0]
        for j in range(ref_index-5,ref_index+5):
            if j>=0 and j<len(ptslist_target):
                prev_pts.append(ptslist_target[j])
        ###cur_pts###
        if  ptslist_origin[i].edge <>0:
            if ptslist_origin[i].index==len(globalptslist01)-2:
                cur_pts[:] = [globalptslist01[ptslist_origin[i].index-2],globalptslist01[ptslist_origin[i].index-1],globalptslist01[ptslist_origin[i].index+1]]
            if  ptslist_origin[i].index < len(globalptslist01)-2:
                cur_pts[:] = [globalptslist01[ptslist_origin[i].index-1],globalptslist01[ptslist_origin[i].index+1],globalptslist01[ptslist_origin[i].index+2]]
        pt_index = next_pt_index(ptslist_origin[i],cur_pts,prev_pts)
        new_line,new_index,new_num,new_st_point = avoid_intersection_index(ptslist_origin[i],pt_index,prev_pts,cur_pts,ref_lines)
        if rs.CurveLength(new_line) < max(width,height)*2:
            temp_weftslist.append(weft_line_class(new_line,new_index,new_num,new_st_point,ptslist_origin[i].pt,ptslist_origin[i].index,False))##st pt is previous pt and end pt is original pt
            ref_lines.append(weft_line_class(new_line,new_index,new_num,new_st_point,ptslist_origin[i].pt,ptslist_origin[i].index,False))##st pt is previous pt and end pt is original pt
            num_neighbor_a[:] = [k for k in range (0,len(globalptslist01)) if globalptslist01[k].pt==ptslist_origin[i].pt]  # add number of neighbor
            num_neighbor_b[:] = [k for k in range (0,len(globalptslist02)) if globalptslist02[k].pt==new_st_point] 
            if len(num_neighbor_a) <> 0:
                indexlist01_a.extend(num_neighbor_a)
            if len(num_neighbor_b) <> 0:
                indexlist01_b.extend(num_neighbor_b)
    return temp_weftslist,indexlist01_a,indexlist01_b,indexlist02

def dist_curve_to_pt(curve,pt):
    para = rs.CurveClosestPoint(curve,pt)
    pt_on_curve = rs.EvaluateCurve(curve,para) 
    dist = rs.Distance(pt,pt_on_curve)
    return dist


def find_long_line(list_crvs):
    if len(list_crvs)==1:
        long_line = list_crvs[0]
    if len(list_crvs)>1:
        PtsOnCrv = []
        for i in range(0,len(list_crvs)):
            PtsOnCrv.extend(rs.DivideCurve(list_crvs[i],500))  #####????
        long_line = rs.AddPolyline(PtsOnCrv)
    return long_line



###################################################
########Preparation for Wefts Generation###########
###################################################
CurveTree = L
ITV_Al_Warp = ITV01*2
ITV_Al_Weft = ITV02
#####################
# Clean pseodo Warps #
List = []
List[:] = dataTreeToList(CurveTree)
RealList = []
if IsWeftClosed == True:
    Temp = List[0]
    List.append(Temp)
for i in range(0,len(List)):
    RealList.append(find_long_line(List[i]))

###################################################
# define pt class instances + Redraw Pseudo Warps #
###################################################
OriIsoWarpsList = []
PtsList =[]
for i in range(0,len(List)):
    AllPts = []
    AllPts[:] = []
    EdgePts = []
    EdgePts[:] =[]
    TempPtsList = []
    TempPtsList [:] = []
    TempOriIsoWarpsList = []
    for j in range(0,len(List[i])):
        SegNum = seg_num(List[i][j],ITV_Al_Warp)
        Pts = rs.DivideCurve(List[i][j],SegNum)
        AllPts.extend(Pts)
        Joins = []
        if IsWarpClosed == True: #is closed curve or open curve:closed
            for k in range(0,len(Pts)-1):    #closed warp lines
                Line = rs.AddLine(Pts[k],Pts[k+1]) # interior pts
                Joins.append(Line)
                if i == len(Pts)-1 and rs.Distance(Pts[i],Pts[0])< 2*ITV_Al_Warp:
                    Line = rs.AddLine(Pts[i],Pts[0])
                    Joins.append(Line)
            TempOriIsoWarpsList.append(rs.JoinCurves(Joins)[0])
        if IsWarpClosed == False:#is closed curve or open curve:open
            EdgePts.append(rs.CurveStartPoint(List[i][j]))
            EdgePts.append(rs.CurveEndPoint(List[i][j]))
            for k in range(0,len(Pts)-1):      #open warp line
                Line = rs.AddLine(Pts[k],Pts[k+1])
                Joins.append(Line)
            TempOriIsoWarpsList.append(rs.JoinCurves(Joins)[0])
    OriIsoWarpsList.append(TempOriIsoWarpsList)
    for l in range(0,len(AllPts)):
        Pt = rs.AddPoint(AllPts[l])
        if len(EdgePts)<>0:
            TestPts = []
            TestPts[:] = [e for e in EdgePts if rs.Distance(e,Pt)<1e-8]
            if len(TestPts)==1:
                TempPtsList.append(pt_class(Pt,l,i,0,1,-1))
            else:
                TempPtsList.append(pt_class(Pt,l,i,-1,2,-1))
        else:
            TempPtsList.append(pt_class(Pt,l,i,-1,2,-1))
    PtsList.append(TempPtsList)

OriWarpsList= []
for i in range(0,len(List)):
    Temp = []
    Temp[:] = OriIsoWarpsList[i]
    OriWarpsList.extend(Temp)

################################
########wefts Generation########
################################
WeftsList = []
ShortWefts = []
#initial end pts#
if IsWeftClosed == False:
    for i in range (0,len(List)):
        InitEndPts = []
        InitEndPts [:] = [e for e in PtsList[i] if e.num==0 ]
        for j in range(0,len(InitEndPts)):
            for k in range(0,len(PtsList[i])):
                if InitEndPts[j].pt == PtsList[i][k].pt:
                    PtsList[i][k].end = 0

#Edge Wefts#
ShortWefts = []
for i in range (0,len(List)):
    EdgePts = []
    EdgePts[:] = [e for e in PtsList[i] if e.edge == 0] #in case of edge wefts, only consider edge pts
    if i < len(List)-1:
        TargetEdgePts = []
        TargetEdgePts[:] = [e for e in PtsList[i+1] if e.edge == 0] 
        TempWeftsList = []
        IndexOfOperatedPts01 = []
        IndexOfOperatedPts02 = []
        IndexOfEndPts = []
        TempWeftsList[:],IndexOfOperatedPts01[:],IndexOfOperatedPts02[:],IndexOfEndPts[:]= wefts_list_to_next(EdgePts,TargetEdgePts,PtsList[i],PtsList[i+1],ITV_Al_Weft,ITV_Al_Warp,RealList)
        ShortWefts.append(TempWeftsList)
        for j in range (0,len(IndexOfOperatedPts01)):
            PtsList[i][IndexOfOperatedPts01[j]].neighbor  = PtsList[i][IndexOfOperatedPts01[j]].neighbor + 1 #while is edge Wefts don't consider situation of end pt
        for j in range (0,len(IndexOfOperatedPts02)):
            PtsList[i+1][IndexOfOperatedPts02[j]].neighbor  = PtsList[i+1][IndexOfOperatedPts02[j]].neighbor + 1 #while is edge Wefts don't consider situation of end pt
        for j in range (0,len(IndexOfEndPts)):
            PtsList[i][IndexOfEndPts[j]].end = 0
    if i == len(List)-1:
        for j in range (0,len(List[i])):
            PtsList[i][j].end = 0



#Interior Wefts#
for i in range (0,len(List)):
    InPts = []
    InPts[:] = [e for e in PtsList[i] if e.edge == -1] #in case of interior wefts, only consider interior pts
    if i<len(List)-1:
        TargetPts = []
        TargetPts[:] = [e for e in PtsList[i+1]] 
        TempWeftsList = []
        IndexOfOperatedPts01 = []
        IndexOfOperatedPts02 = []
        IndexOfEndPts = []
        TempWeftsList[:],IndexOfOperatedPts01[:],IndexOfOperatedPts02[:],IndexOfEndPts[:] = wefts_list_to_next(InPts,TargetPts,PtsList[i],PtsList[i+1],ITV_Al_Weft,ITV_Al_Warp,RealList)
        ShortWefts[i].extend(TempWeftsList)
        for j in range (0,len(IndexOfOperatedPts01)):
            PtsList[i][IndexOfOperatedPts01[j]].neighbor  = PtsList[i][IndexOfOperatedPts01[j]].neighbor + 1
        for j in range (0,len(IndexOfOperatedPts02)):
            PtsList[i+1][IndexOfOperatedPts02[j]].neighbor  = PtsList[i+1][IndexOfOperatedPts02[j]].neighbor + 1
        for j in range (0,len(IndexOfEndPts)):
            PtsList[i][IndexOfEndPts[j]].end = 0
    if i==len(List)-1:
        for j in range( 0,len(PtsList[i])):
            PtsList[i][j].end = 0




#interor wefts needed to be added on prev direction#
for i in range (0,len(List)):
    InPtsNeedAdd = []
    InPtsNeedAdd[:] = [e for e in PtsList[i] if e.neighbor<=3 and e.end<>0 and e.edge<>0 ] # don't consider situation of end pt or edge pt
    TargetPts = []
    TargetPts[:] = PtsList[i-1]
    TempWeftsList = []
    IndexOfOperatedPts01 = []
    IndexOfOperatedPts02 = []
    IndexOfEndPts = []
    TempWeftsList[:],IndexOfOperatedPts01[:],IndexOfOperatedPts02[:],IndexOfEndPts[:] = wefts_list_to_prev(InPtsNeedAdd,TargetPts,PtsList[i],PtsList[i-1],ITV_Al_Weft,ITV_Al_Warp,ShortWefts[i-1])
    ShortWefts[i-1].extend(TempWeftsList)
    for j in range (0,len(IndexOfOperatedPts01)):
       PtsList[i][IndexOfOperatedPts01[j]].neighbor  = PtsList[i][IndexOfOperatedPts01[j]].neighbor + 1
    for j in range (0,len(IndexOfOperatedPts02)):
       PtsList[i-1][IndexOfOperatedPts02[j]].neighbor  = PtsList[i-1][IndexOfOperatedPts02[j]].neighbor + 1




# EndPts need to be add on prev direction
for i in range (0,len(List)):
    EndPtsNeedAdd = []
    EndPtsNeedAdd[:] = [e for e in PtsList[i] if e.end ==0 and e.neighbor<3 and e.edge <>0]
    TargetPts = []
    TargetPts[:] = PtsList[i-1]
    TempWeftsList = []
    IndexOfOperatedPts01 = []
    IndexOfOperatedPts02 = []
    IndexOfEndPts = []
    TempWeftsList[:],IndexOfOperatedPts01[:],IndexOfOperatedPts02[:],IndexOfEndPts[:] = wefts_list_to_prev(EndPtsNeedAdd,TargetPts,PtsList[i],PtsList[i-1],ITV_Al_Weft,ITV_Al_Warp,ShortWefts[i-1])
    ShortWefts[i-1].extend(TempWeftsList)
    for j in range (0,len(IndexOfOperatedPts01)):
        PtsList[i][IndexOfOperatedPts01[j]].neighbor  = PtsList[i][IndexOfOperatedPts01[j]].neighbor + 1 
    for j in range (0,len(IndexOfOperatedPts02)):
        PtsList[i-1][IndexOfOperatedPts02[j]].neighbor  = PtsList[i-1][IndexOfOperatedPts02[j]].neighbor + 1 


#OutPut Ori Short Wefts#
OriPtsOnWarps = []
for i in range (0,len(List)):
    TempPts = []
    TempPts[:] = [e.pt for e in PtsList[i]]
    OriPtsOnWarps.extend(TempPts)
OriWeftsList = []
for i in range (0,(len(List))):
    TempWefts = []
    if i <len(List)-1:
        ShortWefts[i].sort(key=lambda x:(x.index*1000 + x.end_pt_index), reverse=False)
        TempWefts[:] = [e.weft_line for e in ShortWefts[i] if e.weft_line<>0 ]
        OriWeftsList.extend(TempWefts)



#in situation that two triangular is next to each other
for i in range (0,len(List)-1):
    for j in range (0,len(ShortWefts[i])):
        TestObjects = []
        TestObjects[:] = [e for e in ShortWefts[i] if  (e.index==ShortWefts[i][j].index+1 or e.index==ShortWefts[i][j].index-1 or(e.index==ShortWefts[i][j].index and e.end_pt_index<>ShortWefts[i][j].end_pt_index) )]
        ClosestObjectsStPt = []
        ClosestObjectsStPt[:] = [e.index for e in TestObjects]
        ClosestObjectsEndPt = []
        ClosestObjectsEndPt[:] = [e.end_pt_index for e in TestObjects]
        if ShortWefts[i][j].index in ClosestObjectsStPt and ShortWefts[i][j].end_pt_index in ClosestObjectsEndPt:
            ShortWefts[i][j].weft_line = 0
            ShortWefts[i][j].index = -2 #in case of V in W situation
            ShortWefts[i][j].end_pt_index = -2 #in case of V in W situation

#OutPut Ori Short Wefts#
OriPtsOnWarps = []
for i in range (0,len(List)):
    TempPts = []
    TempPts[:] = [e.pt for e in PtsList[i]]
    OriPtsOnWarps.extend(TempPts)
OriWeftsList = []
for i in range (0,(len(List))):
    TempWefts = []
    if i <len(List)-1:
        ShortWefts[i].sort(key=lambda x:(x.index*1000 + x.end_pt_index), reverse=False)
        TempWefts[:] = [e.weft_line for e in ShortWefts[i] if e.weft_line<>0 ]
        OriWeftsList.extend(TempWefts)


##############################
#########sort wefts"##########
##############################
FirstRow = []
FirstRow[:] = [e for e in ShortWefts[0] if e.weft_line<>0]
FirstRow.sort(key=lambda x:(x.index*10000+ x.end_pt_index), reverse=False)# in case two or more first row share same weft num
RealFirstRow = []  # in case two or more first row share same weft num
for i in range(0,len(FirstRow)):
    RealFirstRow.append(weft_class(FirstRow[i].weft_line,i,0,FirstRow[i].st_pt,FirstRow[i].end_pt))
TempWeftsList = []
CurRow = []
NextRow = []
NextWefts = []
for i in range(0,len(RealFirstRow)):
    CurRow[:] = []
    CurRow.append(RealFirstRow[i])# CurRow is a list containing list of weft_class        
    Limit = 0
    Times = 1
    NextRow[:] = []
    NextWefts[:] = []
    Test = []
    while len(CurRow)>0: 
        for j in range (0,len(CurRow)): 
            ForJoinCrvs = []
            ForJoinCrvs[:] = []
            if CurRow[j].num == len(ShortWefts)-1 :
                NextRow.append(weft_class(CurRow[j].weft,CurRow[j].index,CurRow[j].num,CurRow[j].st_pt,CurRow[j].end_pt))
            if CurRow[j].num < len(ShortWefts)-1 :
                NextWefts[:] = [e for e in ShortWefts[CurRow[j].num+1] if e.weft_line<>0 and rs.Distance(e.st_pt ,CurRow[j].end_pt)<1e-6 ] #NextWeft is a list containing list of weft_line_class)
                if len(NextWefts) == 0:
                    NextRow.append(weft_class(CurRow[j].weft,CurRow[j].index,CurRow[j].num,CurRow[j].st_pt,CurRow[j].end_pt)) #!!!otherwise when each branch is of different length, the shortest branch will becom blank
                if len(NextWefts) == 1:
                    ForJoinCrvs[:] = [CurRow[j].weft,NextWefts[0].weft_line]
                    JoinCrvs = rs.JoinCurves(ForJoinCrvs,False)[0] # notice the way joincrvs is used 
                    NextRow.append(weft_class(JoinCrvs,CurRow[j].index,NextWefts[0].num,CurRow[j].st_pt,NextWefts[0].end_pt))
                if len(NextWefts) > 1 :
                    NextWefts.sort(key=lambda x:x.end_pt_index, reverse=False)
                    for k in range(0,len(NextWefts)):
                        if  NextWefts[k].counted_bool == False or (NextWefts[k].counted_bool == True and k == len(NextWefts)-1) :# in case of repetitive loop of long wefts : endPts should not be the same,while same pick the closest nextweft
                            ForJoinCrvs[:] = [CurRow[j].weft,NextWefts[k].weft_line]
                            JoinCrvs = rs.JoinCurves(ForJoinCrvs,False)[0]
                            Index = CurRow[j].index +(pow((1/len(NextWefts)),Times)*k)
                            NextWefts[k].counted_bool = True
                            NextRow.append(weft_class(JoinCrvs,Index,NextWefts[k].num,CurRow[j].st_pt,NextWefts[k].end_pt))
                    Times = Times+1
        Limit += 1 
        if Limit == len(List)+1:
            break
        else:
            CurRow[:] = []
            CurRow[:]= NextRow
            NextRow[:] = []
            NextWefts[:] = []
    TempWeftsList.extend(CurRow)
TempWeftsList.sort(key=lambda x: x.index, reverse=False)
SortWeftsList = []
SortWeftsList[:] =[e.weft for e in TempWeftsList]

###################################################################
######## 1st Adjust: Adjust TempWeftsList to "connect them"########
###################################################################
#Adjust PtsList#
AdjustPtsList = []
for i in range(0,len(SortWeftsList)):
    TempAdjustPtsList = []
    TempPts = []
    TempPts.extend(rs.PolylineVertices(SortWeftsList[i]))
    TempPts.sort(key=lambda x:rs.CurveClosestPoint(SortWeftsList[i],x) , reverse= False)
    for j in range (0,len(OriIsoWarpsList)):
        for k in range(0,len(OriIsoWarpsList[j])):
            if rs.CurveCurveIntersection(SortWeftsList[i],OriIsoWarpsList[j][k]) <> None: 
                TempPt = rs.CurveCurveIntersection(SortWeftsList[i],OriIsoWarpsList[j][k])[0][1]
                TempAdjustPtsList.append(simple_pt_class(TempPt,i,j))
    AdjustPtsList.append(TempAdjustPtsList)


#ForTest=[]
####Adjust Wefts###
#Judging#
JudgePtsList = []
ShortPtsList = []
for i in range(0,len(AdjustPtsList)):
    TempJudgePtsList = []
    TempJudgePtsList[:] = []
    for j in range(0,len(AdjustPtsList[i])):
        Pt = AdjustPtsList[i][j].pt
        #TopPt#
        if i<len(AdjustPtsList)-1 :
            if j<len(AdjustPtsList[i+1]):
                TopPt = AdjustPtsList[i+1][j].pt
            if j>=len(AdjustPtsList[i+1]):
                TopPt =None
        if i >= len(AdjustPtsList)-1:
            TopPt = None
        #TopNextPt#
        if i<len(AdjustPtsList)-1 :
            if j+1 <  len(AdjustPtsList[i+1]):
                TopNextPt = AdjustPtsList[i+1][j+1].pt
            if j+1 >=  len(AdjustPtsList[i+1]):
                TopNextPt = None
        if i>=len(AdjustPtsList)-1:
            TopNextPt = None
        #NextPt#
        if j+1 <len(AdjustPtsList[i]) :
            NextPt = AdjustPtsList[i][j+1].pt
        if j+1 >=len(AdjustPtsList[i]):
            NextPt = None
        if TopPt<>None and TopNextPt<>None and NextPt<>None and rs.Distance(Pt,NextPt)< max(ITV_Al_Weft,ITV_Al_Warp)*3 and rs.Distance(TopPt,TopNextPt) < max(ITV_Al_Weft,ITV_Al_Warp)*3:
            #MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
            #MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
            #CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02)) 
            if rs.Distance(Pt,TopPt)>1e-1:
                warp01 = True
            if rs.Distance(Pt,TopPt)<= 1e-1:
                warp01 = False
            if rs.Distance(NextPt,TopNextPt)>1e-1:
                warp02 = True
            if rs.Distance(NextPt,TopNextPt)<=1e-1:
                warp02 = False
            if rs.Distance(Pt,NextPt)>1e-1:
                weft01 =True
            if rs.Distance(Pt,NextPt)<=1e-1:
                weft01 =False
            if rs.Distance(TopPt,TopNextPt)>1e-1:
                weft02 = True
            if rs.Distance(TopPt,TopNextPt)<=1e-1:
                weft02 = False
            if weft01 ==True and weft02 ==True and warp01==True and warp02 ==True:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02)) 
                TempJudgePtsList.append(sort_pt_class(Pt,CenterPt,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,10.0,10.0,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==False and warp02 ==True:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02)) 
                TempJudgePtsList.append(sort_pt_class(Pt,CenterPt,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,7.5,7.5,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==True and warp02 ==False:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02)) 
                TempJudgePtsList.append(sort_pt_class(Pt,CenterPt,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,7.0,7.0,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==False and warp02 ==False:
                TempJudgePtsList.append(sort_pt_class(Pt,0,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,2.5,2.5,TopPt,TopNextPt,NextPt))
        if TopPt==None or TopNextPt== None or NextPt==None or rs.Distance(Pt,NextPt)>= max(ITV_Al_Weft,ITV_Al_Warp/2)*2 or rs.Distance(TopPt,TopNextPt) >= max(ITV_Al_Weft,ITV_Al_Warp/2)*2:
            if TopPt<>None and TopNextPt<> None and NextPt==None and rs.Distance(Pt,TopPt) > 1e-1 and rs.Distance(Pt,TopPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*2 and  rs.Distance(Pt,TopNextPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*2 :
                TempJudgePtsList.append(sort_pt_class(Pt,0,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,7.0,7.0,TopPt,TopNextPt,Pt))
            elif TopPt<>None and TopNextPt== None and NextPt<>None and rs.Distance(Pt,TopPt) > 1e-1 and rs.Distance(Pt,TopPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*2 and  rs.Distance(TopPt,NextPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*2 :
                TempJudgePtsList.append(sort_pt_class(Pt,0,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,7.0,7.0,TopPt,TopPt,NextPt))
            else:
                TempJudgePtsList.append(sort_pt_class(Pt,0,AdjustPtsList[i][j].index,AdjustPtsList[i][j].num,0.0,0.0,"Null","Null","Null"))
    JudgePtsList.append(TempJudgePtsList)
    #for k in range (0,len(TempJudgePtsList)):
        #ForTest.append(TempJudgePtsList[k].pt)

#Adjusting#
AdjustAmount = []
for i in range(0,len(JudgePtsList)-3):
    TempCur = []
    TempCur[:] = [j for j in range(0,len(JudgePtsList[i])) if JudgePtsList[i][j].mo_color ==10.0 or JudgePtsList[i][j].mo_color ==7.5 or JudgePtsList[i][j].mo_color ==7.0]
    TempCur.sort(key=lambda x:x, reverse=False)
    TempNext = []
    TempNext[:] = [j for j in range(0,len(JudgePtsList[i+1])) if JudgePtsList[i+1][j].mo_color ==10.0 or JudgePtsList[i+1][j].mo_color ==7.5 or JudgePtsList[i+1][j].mo_color ==7.0]
    TempNext.sort(key=lambda x:x, reverse=False)
    if TempCur[0]<TempNext[0] and TempCur[-1]<TempNext[0] :
        Range = []
        Range[:] = range(TempCur[-1]+1,TempNext[0]+1)
        AdjustAmount.append(len(Range))
        for j in Range:
            RefIndex = i+3
            RefNum = j
            while  RefIndex < len(JudgePtsList)-1:
                if rs.Distance(JudgePtsList[RefIndex][RefNum].pt,JudgePtsList[i+2][RefNum].pt ) >0.1:
                    for k in range(i+2,RefIndex):
                        MidPt = rs.CurveMidPoint(rs.AddLine(JudgePtsList[k][RefNum].pt,JudgePtsList[RefIndex][RefNum].pt))
                        JudgePtsList[k][RefNum].pt = MidPt
                    break
                if rs.Distance(JudgePtsList[RefIndex][RefNum].pt,JudgePtsList[i+2][RefNum].pt ) <= 0.1:
                    RefIndex += 1
                if RefIndex == len(JudgePtsList)-1:
                    break
    if TempCur[0]>TempNext[-1] and TempCur[-1]>TempNext[-1] :
        Range = []
        Range[:] = range(TempNext[-1]+1,TempCur[0]+1)
        AdjustAmount.append(len(Range))
        for j in Range:
            RefIndex = i+3
            RefNum =j
            while RefIndex < len(JudgePtsList)-1:
                if rs.Distance(JudgePtsList[RefIndex][RefNum].pt,JudgePtsList[i+1][RefNum].pt ) >0.1:
                    for k in range(i+1,RefIndex):
                        MidPt = rs.CurveMidPoint(rs.AddLine(JudgePtsList[k][RefNum].pt,JudgePtsList[RefIndex][RefNum].pt))
                        JudgePtsList[k][RefNum].pt = MidPt
                    break
                if rs.Distance(JudgePtsList[RefIndex][RefNum].pt,JudgePtsList[i+1][RefNum].pt ) <= 0.1:
                    RefIndex += 1
                if RefIndex == len(JudgePtsList)-1:
                    break

#Output TempAdjustWefts
TempAdjustWeftsList = []
for i in range (0,len(JudgePtsList)):
    TempPts = []
    TempPts[:] = [e.pt for e in JudgePtsList[i]]
    TempWeft = rs.AddPolyline(TempPts)
    TempAdjustWeftsList.append(TempWeft)

#re map ptslist as warp num#
RemapPtsList = []
TestNum = []
for i in range (0,len(JudgePtsList)):
    for j in range(0,len(JudgePtsList[i])):
        if JudgePtsList[i][j].num  not in TestNum:
            NewList = []
            NewList[:] = [JudgePtsList[i][j]]
            RemapPtsList.append(NewList)
            TestNum.append(JudgePtsList[i][j].num)
        if JudgePtsList[i][j].num in TestNum:
            RemapPtsList[JudgePtsList[i][j].num].append(JudgePtsList[i][j])

#local "Relaxation"#
OutPutPts = []
for i in range (0,len(RemapPtsList)):
    TempPts = []
    TempPts[:] = RemapPtsList[i]
    TempPts.sort(key=lambda x:e.index, reverse=False)
    TempLines = []
    TestedPts = []
    TempWarps = []
    for j in range(0,len(TempPts)-1):
        if TempPts[j].index+1 == TempPts[j+1].index and rs.Distance(TempPts[j].pt,TempPts[j+1].pt)>0.01 and rs.Distance(TempPts[j].pt,TempPts[j+1].pt)<2*ITV_Al_Warp:
            TempLine = rs.AddLine(TempPts[j].pt,TempPts[j+1].pt)
            if rs.CurveLength(TempLine)<=ITV_Al_Warp and j not in TestedPts:
                TestedPts.append(j+1)
            TempLines.append(TempLine)
    TempWarps[:] = rs.JoinCurves(TempLines)
    if TestedPts<>[]:
        for k in range(0,len(TempWarps)):
            RefPtsList = []
            RefPtsList.extend(rs.PolylineVertices(TempWarps[k])) 
            for l in range(0,len(TestedPts)):
                if TempPts[TestedPts[l]].pt in RefPtsList :
                    RefIndex = []
                    RefIndex = [m for m in range(0,len(RefPtsList)) if RefPtsList[m] ==  TempPts[TestedPts[l]].pt][0]
                    RefRange = []
                    if RefIndex-2>=0 and RefIndex+2<= len(RefPtsList)-1: # select fromt 3 and back 3 pts
                        RefRange[:] = range(RefIndex-2,RefIndex+3)
                    if RefIndex-2<0 and RefIndex+2<= len(RefPtsList)-1:
                        RefRange[:] = range(0,RefIndex+3)
                    if RefIndex-2>=0 and RefIndex+2 > len(RefPtsList)-1:
                        RefRange[:] = range(RefIndex-2,len(RefPtsList))
                    if RefIndex-2<0 and RefIndex+2 > len(RefPtsList)-1:
                        RefRange[:] = range(0,len(RefPtsList))
                    LocalLines= []
                    for n in range(0,len(RefRange)-1):
                        LocalLine = rs.AddLine(RefPtsList[RefRange[n]],RefPtsList[RefRange[n+1]])
                        LocalLines.append(LocalLine)
                    LocalCurve = rs.JoinCurves(LocalLines)[0]
                    LocalRefPts = []
                    LocalRefPts[:] = rs.PolylineVertices(LocalCurve)
                    DivideCount = len(LocalRefPts)-1
                    NewLocalPts = []
                    NewLocalPts[:] = rs.DivideCurve(LocalCurve,DivideCount)
                    for n in range(0,len(LocalRefPts)):
                        OriPtsListCount = []
                        OriPtsListCount[:] = [p for p in range(0,len(RemapPtsList[i])) if RemapPtsList[i][p].pt == LocalRefPts[n] ]
                        for o in range(0,len(OriPtsListCount)):
                            AdjustCount = OriPtsListCount[o]
                            RemapPtsList[i][AdjustCount].pt = NewLocalPts[n]

#output adjustWarps
AdjustWarpsList = []
AdjustWarpsClasses = []
TempWarpsList = []
for i in range (0,len(RemapPtsList)):
    TempWarps = []
    for j in range(0,len(RemapPtsList[i])-1):
        if rs.Distance(RemapPtsList[i][j].pt,RemapPtsList[i][j+1].pt)>0.01 and rs.Distance(RemapPtsList[i][j].pt,RemapPtsList[i][j+1].pt)<2*ITV_Al_Warp:
            TempWarp = rs.AddLine(RemapPtsList[i][j].pt,RemapPtsList[i][j+1].pt)
            TempWarps.append(TempWarp)
    TempWarpsList[:] = rs.JoinCurves(TempWarps)
    for j in range(0,len(TempWarpsList)):
        AdjustWarpsList.append(TempWarpsList[j])
        AdjustWarpsClasses.append(warp_class(TempWarpsList[j],i))

#remap ptslist as weft index#
RelaxedPtsList = []
TestIndex= []
for i in range (0,len(RemapPtsList)):
    for j in range(0,len(RemapPtsList[i])):
        if RemapPtsList[i][j].index not in TestIndex:
            NewList = []
            NewList[:] = [RemapPtsList[i][j]]
            RelaxedPtsList.append(NewList)
            TestIndex.append(RemapPtsList[i][j].index)
        if RemapPtsList[i][j].index in TestIndex:
            RelaxedPtsList[RemapPtsList[i][j].index].append(RemapPtsList[i][j])

AdjustWeftsClasses=[]
AdjustWeftsList = []
for i in range (0,len(RelaxedPtsList)):
    RelaxedPtsList[i].sort(key=lambda x:x.num,reverse=False)
    TempPts = []
    TempPts[:] = [e.pt for e in RelaxedPtsList[i]]
    TempWeft = rs.AddPolyline(TempPts)
    AdjustWeftsList.append(TempWeft)
    AdjustWeftsClasses.append(weft_class(TempWeft,i,0,0,0))

#######################################
###Add Double Wefts for Knitability ###
#######################################
#add wefts#
for i in range(0,len(AdjustWeftsClasses)-1):
    TempPts01 = []
    TempPts01[:] = rs.PolylineVertices( AdjustWeftsClasses[i].weft)
    TempPts02 = []
    TempPts03 = []
    TempPts03[:] = rs.PolylineVertices( AdjustWeftsClasses[i+1].weft)
    if len(TempPts01)<=len(TempPts03):
        Count = len(TempPts01)
    if len(TempPts01)>len(TempPts03):
        Count = len(TempPts03)
    for j in range(0,Count):
        if rs.Distance(TempPts01[j],TempPts03[j])>=1e-1:
            TempPt = rs.CurveMidPoint(rs.AddLine(TempPts01[j],TempPts03[j]))
            TempPts02.append(TempPt)
        if rs.Distance(TempPts01[j],TempPts03[j])<1e-1:
            TempPt = TempPts01[j]
            TempPts02.append(TempPt)
    NewWeft = rs.AddPolyline(TempPts02)
    AdjustWeftsClasses.append(weft_class(NewWeft,i+0.5,0,0,0))
    #if IsWarpClosed == True and i == len(AdjustWeftsClasses)-2:#add extra curve
    #    TempPts01 = []
    #    TempPts01[:] = rs.PolylineVertices( AdjustWeftsClasses[len(AdjustWeftsClasses)-1].weft)
    #    TempPts02 = []
    #    TempPts03 = []
    #    TempPts03[:] = rs.PolylineVertices( AdjustWeftsClasses[0].weft)
    #    if len(TempPts01)<=len(TempPts03):
    #        Count = len(TempPts01)
    #    if len(TempPts01)>len(TempPts03):
    #        Count = len(TempPts03)
    #    for j in range(0,Count):
    #        TempPt = rs.CurveMidPoint(rs.AddLine(TempPts01[j],TempPts03[j]))
    #        TempPts02.append(TempPt)
    #    NewWeft = rs.AddPolyline(TempPts02)
    #    AdjustWeftsClasses.append(weft_class(NewWeft,len(AdjustWeftsClasses)-0.5,0,0,0))
AdjustWeftsClasses.sort(key=lambda x: x.index, reverse=False)
WeftsList[:] = [e.weft for e in  AdjustWeftsClasses]

#remapp the Added PtsList #
AddedPtsList = []
for i in range(0,len(WeftsList)):
    TempAddedPtsList = []
    TempPts = []
    TempPts.extend( rs.PolylineVertices(WeftsList[i]))
    TempPts.sort(key=lambda x:rs.CurveClosestPoint(WeftsList[i],x) , reverse= False)
    for j in range (0,len(AdjustWarpsList)):
        if rs.CurveCurveIntersection(WeftsList[i],AdjustWarpsList[j]) <> None: 
            TempPt = rs.CurveCurveIntersection(WeftsList[i],AdjustWarpsList[j])[0][1]
            TempWarpNum = AdjustWarpsClasses[j].num
            TempAddedPtsList.append(simple_pt_class(TempPt,i,TempWarpNum))
    AddedPtsList.append(TempAddedPtsList)

##########################################
######## Generate Knitting Pattern########
##########################################
#generate initial 2D pattern
ForOutPut = []
ForOutPut[:] = []
ShortPtsList = []
for i in range(0,len(AddedPtsList)):
    TempForOutPut = []
    TempForOutPut[:] = []
    for j in range(0,len(AddedPtsList[i])):
        Pt = AddedPtsList[i][j].pt
        #TopPt#
        if i<len(AddedPtsList)-1 :
            if j<len(AddedPtsList[i+1]):
                TopPt = AddedPtsList[i+1][j].pt
            if j>=len(AddedPtsList[i+1]):
                TopPt =None
        if i >= len(AddedPtsList)-1:
            TopPt = None
        #TopNextPt#
        if i<len(AddedPtsList)-1 :
            if j+1 <  len(AddedPtsList[i+1]):
                TopNextPt = AddedPtsList[i+1][j+1].pt
            if j+1 >=  len(AddedPtsList[i+1]):
                TopNextPt = None
        if i>=len(AddedPtsList)-1:
            TopNextPt = None
        #NextPt#
        if j+1 <len(AddedPtsList[i]) :
            NextPt = AddedPtsList[i][j+1].pt
        if j+1 >=len(AddedPtsList[i]):
            NextPt = None
        if TopPt<>None and TopNextPt<>None and NextPt<>None and rs.Distance(Pt,NextPt)< max(ITV_Al_Weft,ITV_Al_Warp/2)*3 and rs.Distance(TopPt,TopNextPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*3:
            if rs.Distance(Pt,TopPt)>1e-1:
                warp01 = True
            if rs.Distance(Pt,TopPt)<= 1e-1:
                warp01 = False
            if rs.Distance(NextPt,TopNextPt)>1e-1:
                warp02 = True
            if rs.Distance(NextPt,TopNextPt)<=1e-1:
                warp02 = False
            if rs.Distance(Pt,NextPt)>1e-1:
                weft01 =True
            if rs.Distance(Pt,NextPt)<=1e-1:
                weft01 =False
            if rs.Distance(TopPt,TopNextPt)>1e-1:
                weft02 = True
            if rs.Distance(TopPt,TopNextPt)<=1e-1:
                weft02 = False
            if weft01 ==True and weft02 ==True and warp01==True and warp02 ==True:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02))
                TempForOutPut.append(sort_pt_class(Pt,CenterPt,AddedPtsList[i][j].index,AddedPtsList[i][j].num,10.0,10.0,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==False and warp02 ==True:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02))
                TempForOutPut.append(sort_pt_class(Pt,CenterPt,AddedPtsList[i][j].index,AddedPtsList[i][j].num,7.5,7.5,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==True and warp02 ==False:
                MidPt01 = rs.CurveMidPoint(rs.AddLine(Pt,NextPt))
                MidPt02 = rs.CurveMidPoint(rs.AddLine(TopPt,TopNextPt))
                CenterPt = rs.CurveMidPoint(rs.AddLine(MidPt01,MidPt02))
                TempForOutPut.append(sort_pt_class(Pt,CenterPt,AddedPtsList[i][j].index,AddedPtsList[i][j].num,7.0,7.0,TopPt,TopNextPt,NextPt))
            if weft01 ==True and weft02 ==True and warp01==False and warp02 ==False:
               TempForOutPut.append(sort_pt_class(Pt,0,AddedPtsList[i][j].index,AddedPtsList[i][j].num,2.5,2.5,TopPt,TopNextPt,NextPt))
        if TopPt==None or TopNextPt== None or NextPt==None or rs.Distance(Pt,NextPt)>= max(ITV_Al_Weft,ITV_Al_Warp/2)*3 or rs.Distance(TopPt,TopNextPt) >= max(ITV_Al_Weft,ITV_Al_Warp/2)*3:
            if TopPt<>None and TopNextPt<> None and NextPt==None and rs.Distance(Pt,TopPt) > 1e-1 and rs.Distance(Pt,TopPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*3 and  rs.Distance(Pt,TopNextPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*3 :
                TempForOutPut.append(sort_pt_class(Pt,0,AddedPtsList[i][j].index,AddedPtsList[i][j].num,7.0,7.0,TopPt,TopNextPt,Pt))
            elif TopPt<>None and TopNextPt== None and NextPt<>None and rs.Distance(Pt,TopPt) > 1e-1 and rs.Distance(Pt,TopPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*3 and  rs.Distance(TopPt,NextPt) < max(ITV_Al_Weft,ITV_Al_Warp/2)*3 :
                TempForOutPut.append(sort_pt_class(Pt,0,AddedPtsList[i][j].index,AddedPtsList[i][j].num,7.0,7.0,TopPt,TopPt,NextPt))
            else:
                TempForOutPut.append(sort_pt_class(Pt,0,AddedPtsList[i][j].index,AddedPtsList[i][j].num,0.0,0.0,"Null","Null","Null"))
    ForOutPut.append(TempForOutPut)

#output initial 2D pattern
WeftIndex = []
WarpNum = []
Type = []      
for i in range(0,len(ForOutPut)):
    for j in range(0,len(ForOutPut[i])):
        WeftIndex .append(ForOutPut[i][j].index)
        WarpNum.append(ForOutPut[i][j].num)
        Type.append(ForOutPut[i][j].color)


###adjust 2D pattern and Weftlines###
AdjustList = []
for i in range(0,len(ForOutPut)-3):
    if i %2 <>0:
        #pattern color on each row
        TempCur = []
        TempCur[:] = [j for j in range(0,len(ForOutPut[i])) if ForOutPut[i][j].mo_color ==10.0 or ForOutPut[i][j].mo_color ==7.5 or ForOutPut[i][j].mo_color ==7.0]
        TempCur.sort(key=lambda x:x, reverse=False)
        TempNext = []
        TempNext[:] = [j for j in range(0,len(ForOutPut[i+1])) if ForOutPut[i+1][j].mo_color ==10.0 or ForOutPut[i+1][j].mo_color ==7.5 or ForOutPut[i+1][j].mo_color ==7.0]
        TempNext.sort(key=lambda x:x, reverse=False)
        if TempCur[0] < TempNext[0]:  # i is longer
            Small = TempCur[0]
            Big = TempNext[0]
            ChangeRange = []
            ChangeRange = range(Small,Big+1)
            for j in range(0,len(ChangeRange)): 
                PtOnI = ForOutPut[i][ChangeRange[j]].pt
                if j<>len(ChangeRange)-1:
                    #move pts and neighbors
                    ForOutPut[i][ChangeRange[j]].top = PtOnI
                    ForOutPut[i][ChangeRange[j]].top_next = ForOutPut[i][ChangeRange[j+1]].pt
                    ForOutPut[i+1][ChangeRange[j]].pt = PtOnI
                    ForOutPut[i+1][ChangeRange[j]].top = PtOnI
                    ForOutPut[i+1][ChangeRange[j]].top_next = ForOutPut[i][ChangeRange[j+1]].pt
                    ForOutPut[i+1][ChangeRange[j]].next = ForOutPut[i][ChangeRange[j+1]].pt
                    ForOutPut[i+2][ChangeRange[j]].pt = PtOnI
                    ForOutPut[i+2][ChangeRange[j]].next = ForOutPut[i][ChangeRange[j+1]].pt
                    #change center pts
                    ForOutPut[i][ChangeRange[j]].center_pt = 0
                    ForOutPut[i+2][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].pt,ForOutPut[i+2][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].top,ForOutPut[i+2][ChangeRange[j]].top_next))))
                    #change color
                    ForOutPut[i][ChangeRange[j]].mo_color = 2.5
                    ForOutPut[i+2][ChangeRange[j]].mo_color = 10.0
                    if j == 0  and rs.Distance(ForOutPut[i+2][ChangeRange[j]].pt,ForOutPut[i+2][ChangeRange[j]].top)<0.1:
                        ForOutPut[i+2][ChangeRange[j]].mo_color = 7.5
                if j == len(ChangeRange)-1:
                    #move pts and neighbors
                    ForOutPut[i][ChangeRange[j]].top = PtOnI
                    ForOutPut[i+1][ChangeRange[j]].pt = PtOnI
                    ForOutPut[i+1][ChangeRange[j]].top = PtOnI
                    ForOutPut[i+2][ChangeRange[j]].pt = PtOnI
                    #change center pts
                    ForOutPut[i][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].pt,ForOutPut[i][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].top,ForOutPut[i][ChangeRange[j]].top_next))))
                    ForOutPut[i+1][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i+1][ChangeRange[j]].pt,ForOutPut[i+1][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i+1][ChangeRange[j]].top,ForOutPut[i+1][ChangeRange[j]].top_next))))
                    ForOutPut[i+2][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].pt,ForOutPut[i+2][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].top,ForOutPut[i+2][ChangeRange[j]].top_next))))
                    #change color
                    ForOutPut[i][ChangeRange[j]].mo_color = 7.5
                    ForOutPut[i+2][ChangeRange[j]].mo_color = 10.0
        if TempCur[0] > TempNext[0]:  # i is shorter
            Small = TempNext[0]
            Big = TempCur[0]
            ChangeRange = []
            ChangeRange = range(Small,Big+1)
            for j in range(0,len(ChangeRange)): 
                PtOnIandTwo = ForOutPut[i+2][ChangeRange[j]].pt
                PtOnIandThree = ForOutPut[i+3][ChangeRange[j]].pt
                if j < len(ChangeRange)-1:
                    #move pts and neighbors
                    ForOutPut[i][ChangeRange[j]].top = PtOnIandTwo
                    ForOutPut[i][ChangeRange[j]].top_next = ForOutPut[i+2][ChangeRange[j+1]].pt
                    ForOutPut[i+1][ChangeRange[j]].pt = PtOnIandTwo
                    ForOutPut[i+1][ChangeRange[j]].top = PtOnIandThree
                    ForOutPut[i+1][ChangeRange[j]].top_next = ForOutPut[i+3][ChangeRange[j+1]].pt
                    ForOutPut[i+1][ChangeRange[j]].next = ForOutPut[i+2][ChangeRange[j+1]].pt
                    ForOutPut[i+2][ChangeRange[j]].pt = PtOnIandThree
                    ForOutPut[i+2][ChangeRange[j]].next = ForOutPut[i+3][ChangeRange[j+1]].pt
                    #change center pts
                    ForOutPut[i][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].pt,ForOutPut[i][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].top,ForOutPut[i][ChangeRange[j]].top_next))))
                    ForOutPut[i+2][ChangeRange[j]].center_pt = 0 
                    #change color
                    ForOutPut[i][ChangeRange[j]].mo_color = 10.0
                    ForOutPut[i+2][ChangeRange[j]].mo_color = 2.5
                    if j==0  and rs.Distance(ForOutPut[i][ChangeRange[j]].pt, ForOutPut[i][ChangeRange[j]].top)<0.1:
                        ForOutPut[i][ChangeRange[j]].mo_color = 7.5
                if j == len(ChangeRange)-1:
                    #move pts and neighbors
                    ForOutPut[i][ChangeRange[j]].top = PtOnIandTwo
                    ForOutPut[i+1][ChangeRange[j]].pt = PtOnIandTwo
                    ForOutPut[i+1][ChangeRange[j]].top = PtOnIandThree
                    ForOutPut[i+2][ChangeRange[j]].pt = PtOnIandThree
                    #change center pts
                    ForOutPut[i][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].pt,ForOutPut[i][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i][ChangeRange[j]].top,ForOutPut[i][ChangeRange[j]].top_next))))
                    ForOutPut[i+1][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i+1][ChangeRange[j]].pt,ForOutPut[i+1][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i+1][ChangeRange[j]].top,ForOutPut[i+1][ChangeRange[j]].top_next))))
                    ForOutPut[i+2][ChangeRange[j]].center_pt = rs.CurveMidPoint(rs.AddLine(rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].pt,ForOutPut[i+2][ChangeRange[j]].next)),rs.CurveMidPoint(rs.AddLine(ForOutPut[i+2][ChangeRange[j]].top,ForOutPut[i+2][ChangeRange[j]].top_next))))
                    #change color
                    ForOutPut[i][ChangeRange[j]].mo_color = 10.0
                    ForOutPut[i+2][ChangeRange[j]].mo_color = 7.5


##output adjust wefts ##
FinalWeftsList = []
for i in range(0,len(ForOutPut)):
    TempPts = []
    TempPts[:] = [e.pt for e in ForOutPut[i]]
    TempWeft = rs.AddPolyline(TempPts)
    FinalWeftsList.append(TempWeft)

##output adjust 2D pattern##
MoWarpIndex = []
MoWeftNum = []
MoType = []
for i in range(0,len(ForOutPut)):
    for j in range(0,len(ForOutPut[i])):
        MoWarpIndex.append(ForOutPut[i][j].index)
        MoWeftNum.append(ForOutPut[i][j].num)
        MoType.append(ForOutPut[i][j].mo_color)

##generate knitting path##
SpatialCenterPts = []
CenterPtsIndex = []
CenterPtsNum = []
for i in range(0,len(ForOutPut)):
    Temp = []
    Temp[:] =[e for e in  ForOutPut[i] if e.mo_color == 10.0 or e.mo_color == 7.5 or e.mo_color == 7.0]
    if i%2 == 0:
        Temp.sort(key= lambda x:x.num, reverse = False)
    if i%2 <> 0:
        Temp.sort(key= lambda x:x.num, reverse = True)
    TempCenterPts = []
    TempCenterPts[:] = [e.center_pt for e in Temp]
    TempIndex = []
    TempIndex[:] = [e.index+0.4 for e in Temp]
    TempNum = []
    TempNum[:] = [e.num+0.4 for e in Temp]
    SpatialCenterPts.extend(TempCenterPts)
    CenterPtsIndex.extend(TempIndex)
    CenterPtsNum.extend(TempNum)


for i in range(0,len(ForOutPut)):
    ForOutPut[i].sort(key= lambda x:x.index*1000000 + x.num, reverse = False)

##output##
ForTest = []
for i in range(0,len(ForOutPut)):
    for j in range(0,len(ForOutPut[i])):
        TempPt = ForOutPut[i][j].pt
        TempTopPt = ForOutPut[i][j].top
        TempTopNextPt = ForOutPut[i][j].top_next
        TempNextPt = ForOutPut[i][j].next
        TempType = ForOutPut[i][j].mo_color
        ForTest.append([TempPt,TempTopPt,TempTopNextPt,TempNextPt,TempType,i,j])
ForTest = raggedListToDataTree(ForTest)

