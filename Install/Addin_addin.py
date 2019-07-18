import arcpy
import pythonaddins
import numpy as np

class ButtonClass11(object):
    """Implementation for Addin_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        def PointToPolygon(points):
            poly_string='POLYGON (('
            for i in range(len(points)):
                if i==0:
                    poly_string+=str(points[i][0])
                    poly_string+=' '+str(points[i][1])
                else:
                    poly_string+=', '+str(points[i][0])
                    poly_string+=' '+str(points[i][1])
            poly_string+='))'
            return poly_string

        def polylineToLines(polyline):
            polyline=polyline[17:-1]
            polyline=polyline.split('),')
            if len(polyline)==1:
                return ['LINESTRING'+polyline[0]]
            else:
                lines=[]
                num,idx=len(polyline),0
                for i in range(num):
                    if idx==num-1:
                        lines.append('LINESTRING'+polyline[i])
                    else:
                        lines.append('LINESTRING'+polyline[i]+')')
                    idx+=1
                return lines
                
        
        def lineNum(extent,spacing):
            scope=extent[1]+0.2
            base=scope//spacing
            if base-int(base)==0:
                return base
            else:
                return int(base+1)

        def getCover(extent,n,spacing):
            result=[]
            if extent[0]=='type1':
                for i in range(n):
                    p1=[extent[3]-0.1,extent[5]+i*spacing-0.1]
                    p2=[extent[2]+0.1,extent[5]+i*spacing-0.1]
                    p3=[extent[2]+0.1,extent[5]+(i+1)*spacing-0.1]
                    p4=[extent[3]-0.1,extent[5]+(i+1)*spacing-0.1]
                    wkt_string=PointToPolygon([p1,p2,p3,p4,p1])
                    result.append(arcpy.FromWKT(wkt_string))
            else:
                for i in range(n):
                    p1=[extent[3]+i*spacing-0.1,extent[5]-0.1]
                    p2=[extent[3]+(i+1)*spacing-0.1,extent[5]-0.1]
                    p3=[extent[3]+(i+1)*spacing-0.1,extent[4]+0.1]
                    p4=[extent[3]+i*spacing-0.1,extent[4]+0.1]
                    wkt_string=PointToPolygon([p1,p2,p3,p4,p1])
                    result.append(arcpy.FromWKT(wkt_string))
            return result

        def getPolygon(main,cover):
            try:
                poly_WKT=main.clip(cover.extent).WKT
            except:
                main1=arcpy.FromWKT(main.WKT)
                poly_WKT=main1.clip(cover.extent).WKT
            if 'EMPTY' in poly_WKT:
                return []
            poly_WKT=poly_WKT[14:-1]
            polygons=[]
            temp_poly='POLYGON '
            for i in range(len(poly_WKT)-1):
                temp_poly+=poly_WKT[i]
                if poly_WKT[i]==' ' and poly_WKT[i+1]=='(':
                    temp_poly=temp_poly[0:-2]
                    polygons.append(arcpy.FromWKT(temp_poly))
                    temp_poly='POLYGON '
                    continue
                if i==len(poly_WKT)-2:
                    temp_poly+=')'
                    polygons.append(arcpy.FromWKT(temp_poly))
            return polygons

        def PointToLine(points):
            line='LINESTRING ('
            for i in range(len(points)):
                if i==0:
                    line+=str(points[i][0])
                    line+=' '+str(points[i][1])
                else:
                    line+=', '+str(points[i][0])
                    line+=' '+str(points[i][1])
            line+=')'
            return arcpy.FromWKT(line)

        def getLineBuffer(extent,n,spacing):
            result=[]
            for i in range(n):
                if extent[0]=='type1':
                    p1=[extent[3]-0.1,extent[5]+i*spacing-0.1]
                    p2=[extent[2]+0.1,extent[5]+i*spacing-0.1]
                    line=PointToLine([p1,p2])
                    result.append(line.buffer(0.3))
                else:
                    p1=[extent[3]+i*spacing-0.1,extent[5]-0.1]
                    p2=[extent[3]+i*spacing-0.1,extent[4]+0.1]
                    line=PointToLine([p1,p2])
                    result.append(line.buffer(0.3))
            return result

        def getMedian(vector):
            vector.sort()
            x=int(len(vector)/2)
            if (len(vector)-2*(len(vector)//2))==1:
                return vector[x]
            else:
                return (vector[x-1]+vector[x])/2

        def getLine(extent,points,n):
            lines=[]
            a,b=np.polyfit([points[0],points[2]],[points[1],points[3]],1)
            slope=-1/a
            starting_x,ending_x=min([points[0],points[2]]),max([points[0],points[2]])
            step=(ending_x-starting_x)/(n+1)
            for i in range(n):
                x2=starting_x+(i+1)*step
                y2=a*x2+b
                x1,x3=extent.XMin-0.1,extent.XMax+0.1
                y1=slope*(x1-x2)+y2
                y3=slope*(x3-x2)+y2
                lineStr='LINESTRING ('+str(x1)+' '+str(y1)+', '+str(x3)+' '+str(y3)+')'
                lines.append(arcpy.FromWKT(lineStr))
            return lines

        def isodd(x):
            if x-(x//2)*2==1:
                return True
            else:
                return False

        def getAverageWidth(sel_road,polygons,buffer):
            area,widths=[],[]
            num=len(polygons)
            limit=16
            if num>limit:
                width_idx=np.linspace(1,num,limit)
            else:
                width_idx=np.linspace(1,num,num)
            width_idx=width_idx.tolist()
            ID_length=len(width_idx)
            for ID in range(ID_length):
                width_idx[ID]=int(width_idx[ID])
            for iii in width_idx:
                i=iii-1
                clip_poly=[]
                for j in buffer:
                    temp=getPolygon(polygons[i],j)
                    if len(temp)==2:
                        break
                    if len(temp)==1:
                        clip_poly.append(temp[0])
                if len(clip_poly)!=2:
                    continue
                area.append(polygons[i].area)
                try:
                    p1x,p1y=clip_poly[0].centroid.X,clip_poly[0].centroid.Y
                    p2x,p2y=clip_poly[1].centroid.X,clip_poly[1].centroid.Y
                except:
                    widths.append(0)
                    continue
                n=1
                per_lines=getLine(sel_road.extent,[p1x,p1y,p2x,p2y],n)
                width=[]
                for j in per_lines:
                    POLYGON=arcpy.FromWKT(sel_road.WKT)
                    clip_line=j.intersect(POLYGON,2)
                    poly_to_lines=polylineToLines(clip_line.WKT)
                    if len(poly_to_lines)==1:
                        width.append(clip_line.length)
                    else:
                        for ij in poly_to_lines:
                            string_to_line=arcpy.FromWKT(ij)
                            if string_to_line.crosses(polygons[i]) or string_to_line.within(polygons[i]):
                                width.append(string_to_line.length)
                                break
                tot,count=0,0
                for k in width:
                    tot+=k
                    count+=1
                widths.append(tot/count)
            totArea,result=0,0
            median=getMedian(widths)
            tolerance=3
            for ii in range(len(widths)):
                if widths[ii]>=3*median or widths[ii]<=median/3:
                    continue
                result+=widths[ii]*area[ii]
                totArea+=area[ii]
            return result/totArea
            
        
        
        input_fc=arcpy.env.workspace
        fc1=input_fc.split('\\')
        name1=fc1[-1]
        name=name1+'.shp'
        path=''
        for i in range(len(fc1[0:-1])):
            path+=fc1[i]
            if i != len(fc1[0:-1])-1:
                path+='\\'
        arcpy.env.workspace=path
        field_width='Avg_Width'
        arcpy.AddField_management(name1,field_width,"DOUBLE")
        fc=arcpy.env.workspace+'\\'+name
        cursor=None
        cursor=arcpy.UpdateCursor(fc)
        idx=0
        for road in cursor:
            orientation=[]
            record = road.getValue('shape')
            extent = record.extent
            if (extent.YMax-extent.YMin)>=(extent.XMax-extent.XMin):
                orientation.append(['type1',extent.YMax-extent.YMin,extent.XMax,extent.XMin,extent.YMax,extent.YMin])
            else:
                orientation.append(['type2',extent.XMax-extent.XMin,extent.XMax,extent.XMin,extent.YMax,extent.YMin])
            spacing=int(orientation[0][1]/3)
            if spacing==0:
                SP=orientation[0][1]/3*10
                spacing=int(SP)*0.1
            if spacing>9:
                spacing=9
            n=int(lineNum(orientation[0],spacing))
            cover=getCover(orientation[0],n,spacing)
            small_poly=[]
            for i in cover:
                temp_poly=getPolygon(record,i)
                small_poly.extend(temp_poly)
            buffer=getLineBuffer(orientation[0],n,spacing)
            Width=(getAverageWidth(record,small_poly,buffer))
            road.setValue(field_width,round(Width,1))
            cursor.updateRow(road)
            idx+=1
        
        

class ComboBoxClass2(object):
    """Implementation for Addin_addin.combobox (ComboBox)"""
    def __init__(self):
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWW'
        self.width = 'WWWWWW'
    def onSelChange(self, selection):
        layer = arcpy.mapping.ListLayers(self.mxd, selection)[0]
        arcpy.env.workspace=layer.workspacePath+'\\'+layer.name
        
    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        self.mxd = arcpy.mapping.MapDocument('current')
	layers = arcpy.mapping.ListLayers(self.mxd)
	self.items = []
	for layer in layers:
            self.items.append(layer.name)

    def onEnter(self):
        pass
    def refresh(self):
        pass
