import os
import shutil
from glob import glob
import re
from zipfile import ZipFile
import time



class KmlDesigner():
    def __init__(self, file, 
                 images_folder=None):
        # file kml
        if os.path.splitext(file)[1] == ".kml":
            with open(file, 'r') as file:
                file = file.readlines()
    
        # file kmz       
        elif os.path.splitext(file)[1] == ".kmz":
            if not os.path.exists('tmp'):
                os.makedirs('tmp')
            else:
                directory = os.getcwd() + '/tmp/*'
                for i in glob(directory):
                    if os.path.isfile(i):
                        os.remove(i)
                    else:
                        shutil.rmtree(i)
            
            path = os.path.join(os.getcwd(),'tmp')
            kmz = ZipFile(file, 'r')
            kmz.extractall(path)
            file = ''
            images_folder = ''
            for f in ['tmp/'+i for i in os.listdir(path)]:
                if f.endswith('.kml'):
                    file += f
                elif f.endswith('images'):
                    images_folder += f
            
            with open(file, 'r') as file:
                file = file.readlines()
        
        # some other file
        else:
            print('File must be kml or kmz extention!!!')
        
        
        self.file = file
        self.icon = images_folder
        self.begin = ''.join(re.findall(r'^<.*?>\n<.*?>', ''.join(file[:12]),
                                        flags=re.DOTALL))+'\n <Document>\n'
        
        self.name_p = '  <name>Points</name>\n'
        self.name_l = '  <name>Lines</name>\n'
        self.name_pol = '  <name>Polygons</name>\n'
        
        self.end = '   </Folder>\n </Document>\n</kml>\n'
        self.folder = '   <Folder>\n'
        self.marker = []
        
        self.folder_name = None
        
    # create styles   
    def count_styles(self):
        styles = []
        styleiM_b = []
        styleiM_end = []
        
        marker = self.file[:self.marker[0]-1]
        for ind, i in enumerate(marker, start=1):
            if re.findall(r'<Style id|<StyleMap', i, flags=re.DOTALL):
                styleiM_b.append(ind)
            if re.findall(r'</Style>|</StyleMap>', i, flags=re.DOTALL):   
                styleiM_end.append(ind)
        for n, k in zip(styleiM_b, styleiM_end):
            i = ''.join(marker[n-1:k])
            styles.append(i)
        return styles
    
    # create placemarks  
    def count_placemarks(self):
        placemarks = []
        placemark_end = []
        placemark_b = []
        
        self.marker = placemark_b
        
        for ind, i in enumerate(self.file, start=1):
            if re.findall(r'<Placemark', i, flags=re.DOTALL):
                placemark_b.append(ind)
            if re.findall(r'</Placemark>(|\n)', i, flags=re.DOTALL):    
                placemark_end.append(ind)
        for n, k in zip(placemark_b, placemark_end):
            i = ''.join(self.file[n-1:k])
            placemarks.append(i)
        if placemarks:
            return placemarks
        else:
            print('Your kml file do not have Placemark.\n'
                  'Please check your kml file.\n'
                  'It may have not standard tags system.')

    # reconstruct file for points, lines, polygons       
    def separate_data(self,placemarks,styles):
        
        placemark_point, styles_point = '', ''
        placemark_polygon, styles_polygon = '', ''
        placemark_line, styles_line = '', ''

        for i in placemarks:
            if re.findall(r'<LineString>|<styleUrl>#line', i):
                placemark_line += i
                control_style = ''.join(re.findall(r'<styleUrl>(.*?)</styleUrl>', i))
                description_url = ''.join(re.findall(r'<description.+(https?://\S+)(?=\")', i))
                name = ''.join(re.findall(r'<name>([^<>]*|.+?)</name>', i)) #(.+?) ([^<>]*)
                
            if re.findall(r'<Point>|<styleUrl>#icon', i):
                placemark_point += i
                control_style = re.findall(r'<styleUrl>(.*?)</styleUrl>', i)
                name = re.findall(r'<name>([^<>]*|.+?)</name>', i) #(.+?) ([^<>]*) 
                description_url = re.findall(r'<description.+(https?://\S+)(?=\")', i)
                
            if re.findall(r'<Polygon>|<styleUrl>#PolyStyle|<MultiGeometry>', i):
                placemark_polygon += i
                control_style = re.findall(r'<styleUrl>(.*?)</styleUrl>', i)
                name = re.findall(r'<name>([^<>]*|.+?)</name>', i) #(.+?) ([^<>]*) 
                description_url = re.findall(r'<description.+(https?://\S+)(?=\")', i)   
                
        for b in styles:
            if re.findall(r'<Style id="line|<LineStyle>|line|StyleMap id="line|<styleUrl>#line', b):
                styles_line += b
            if re.findall(r'Style id="icon|<IconStyle>|<Icon>|icon|<StyleMap id="icon|<styleUrl>#icon', b):
                styles_point += b
            if re.findall(r'<Style id="PolyStyle|<PolyStyle>', b):
                styles_polygon += b
        
        # construct whole kml files
        points = self.begin+self.name_p+styles_point+self.folder+placemark_point+self.end
        lines = self.begin+self.name_l+styles_line+self.folder+placemark_line+self.end
        polygons = self.begin+self.name_pol+styles_polygon+self.folder+placemark_polygon+self.end
        
        # return for combinations points, lines or polygons
        if placemark_point and placemark_line and placemark_polygon:
            self.folder_name = ['Points', 'Lines', 'Polygons']
            return [points, lines, polygons]
        if placemark_point and placemark_line:
            self.folder_name = ['Points', 'Lines']
            return [points, lines] 
        if placemark_polygon and placemark_line:
            self.folder_name = ['Polygons', 'Lines']
            return [polygons, lines]
        if placemark_polygon and placemark_point:
            self.folder_name = ['Polygons', 'Points']
            return [polygons, points]
        if placemark_point:
            self.folder_name = ['Points']
            return [points]
        if placemark_polygon:
            self.folder_name = ['Polygons']
            return [polygons]
        if placemark_line:
            self.folder_name = ['Lines']
            return [lines]
        else:
            print("Something goes wrong, plasemark tags was not found")
            
 
    # function divide our input file.
    # if kmz file have image file with icons and kml it split for point.kmz and lines.kmz(lines without icons)
    # if input file is kml class split to point.kml, lines.kml, polygons.kml
    # class add number for new creating kml or kmz file
    
    def folders_split(self, data):
        # function for searching last file in folder and adding nuber +1
        # for numeration files
        def count(path):
            # if path is empty
            if len(os.listdir(path)) == 0:
                return 1
            last_file = max(glob(path+'/*'), key=os.path.getmtime)
            if re.findall(r'\d+', last_file):
                count = re.findall(r'\d+', last_file)
                count = int(''.join(count))
                return count + 1
            else:
                return 1
        # kmz file have images folder for icons    
        if self.icon: 
            for ind, i in enumerate(self.folder_name):
                if not os.path.exists(i):
                    os.makedirs(i)
                    # for points kmz with images(icons) folder
                    if i.lower() == 'points':
                        with open(f'{i}/{i.lower()}.kml', 'w') as f:
                            f.write(data[ind])
                            time.sleep(1) 
                        num = count(i)
                        # creating kmz file
                        with ZipFile(f'{i}/{i.lower()}_{num}.kmz', "w") as kmz:
                            file_n=f'{i}/{i.lower()}.kml'
                            kmz.write(filename=file_n, arcname=os.path.basename(file_n))
                            #print(file_n)
                            for i in glob(f'{self.icon}/*'):
                                #print(os.path.basename(i))
                                kmz.write(filename=i, arcname=f'images/{os.path.basename(i)}')
                    
                    # for points kml (without icon folder)
                    if i.lower() == 'lines':
                        with open(f'{i}/{i.lower()}_{num}.kml', 'w') as f:
                            f.write(data[ind])
                            
                    # for polygons kml(without icon folder)
                    elif i.lower() == 'polygons':
                        with open(f'{i}/{i.lower()}_{num}.kml', 'w') as f:
                            f.write(data[ind])
                else:
                    # for points kmz with images(icons) folder
                    num = count(i)
                    if i.lower() == 'points':
                        with open(f'{i}/{i.lower()}.kml', 'w') as f:
                            f.write(data[ind])
                            time.sleep(1)
                        # creating kmz file
                        with ZipFile(f'{i}/{i.lower()}_{num}.kmz', "w") as kmz:
                            file_n=f'{i}/{i.lower()}.kml'
                            kmz.write(filename=file_n, arcname=os.path.basename(file_n))
                            #print(file_n)
                            for i in glob(f'{self.icon}/*'):
                                #print(os.path.basename(i))
                                kmz.write(filename=i, arcname=f'images/{os.path.basename(i)}')
                    
                    # for lines kml(without icon folder)
                    if i.lower() == 'lines':
                        with open(f'{i}/{i.lower()}_{num}.kml', 'w') as f:
                            f.write(data[ind])
                    
                    # for polygons kml(without icon folder)
                    elif i.lower() == 'polygons':
                        with open(f'{i}/{i.lower()}_{num}.kml', 'w') as f:
                            f.write(data[ind]) 
                            
        # splits only kml files without creating kmz
        else: 
            for ind, i in enumerate(self.folder_name):
                if not os.path.exists(i):
                    os.makedirs(i)
                    num = count(i)
                    with open(f'{i}/{i}_{num}.kml', 'w') as f:
                        f.write(data[ind])
                else:
                    num = count(i)
                    with open(f'{i}/{i}_{num}.kml', 'w') as f:
                        f.write(data[ind])
                        
                        
                        
                        
                        
                        
                        
                        
def main(file=input(' Choose the file with kml\kmz extension ')):
    kml = KmlDesigner(file)
    kml_placemark = kml.count_placemarks()
    kml_styles = kml.count_styles()
    kml_data = kml.separate_data(kml_placemark, kml_styles)
    kml.folders_split(kml_data)

if __name__ == '__main__':
    main()