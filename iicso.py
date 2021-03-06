import os
import json
from collections import defaultdict

class valuePair:
    def __init__(self, name='none', operator=None, value=None):
        self.name = name
        self.operator = operator
        self.value = value
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name+(' '+self.operator if self.operator != None else '')+(' '+self.value if self.value != None else '')

class clausewitzTree:
    def __init__(self, name='none', nodeType=None, parentNode=None, children=None):
        self.name = name
        self.nodeType = nodeType
        self.parentNode = parentNode
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
    def add_child(self,child):
        assert isinstance(child, valuePair) or isinstance(child,clausewitzTree) or isinstance(child,str)
        self.children.append(child)
    def block(self,tabs=0,inclName=True):
        if inclName:
            blockString = "    "*tabs+self.name+" = {\n"
        else:
            tabs = tabs - 1
        for child in self.children:
            if type(child) is valuePair:
                blockString = blockString+"    "*(tabs+1)+str(child)+"\n"
            elif type(child) is clausewitzTree:
                blockString = blockString+child.block(tabs+1)
        if inclName:
            blockString = blockString+"    "*(tabs)+"}\n"
        return blockString

class building:
    def __init__(self, name='none', upkeep=None, produces=None):
        self.name = name
        self.upkeep = []
        self.produces = []
    def __repr__(self):
        return self.name
    def __str__(self):
        returnString = self.name+"\n"+(str(self.upkeep) if self.upkeep != None else "")+"\n"+(str(self.produces) if self.produces != None else "")
        return returnString

        

#Eventually will consider every included mod - for now, just vanilla
install_dir = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stellaris\\"
mod_dir = "C:\\Users\\Skyler\\Documents\\Paradox Interactive\\Stellaris\\mod\\interstellarincorporated\\"
common_dir = install_dir+"common\\"


#Resource list will later be generated by the program as well - this includes only resources the mod will care about
resource_list = ["minerals","alloys","exotic_gases","rare_crystals","volatile_motes","sr_zro","sr_dark_matter","food","consumer_goods","energy"]

#All stellaris directories that have things that affect the mod (incomplete)
common_dirs = ["buildings\\"]#, "country_types\\", "deposits\\", "districts\\", "planet_modifiers\\", "pop_categories\\", "pop_jobs\\", "starbase_modules\\", "static_modifiers\\", "strategic_resources\\", "technology\\", "traditions\\", "traits\\"]

search_exts = [".txt"]
treeList = []
for dir_str in common_dirs:
    directory = os.fsencode(common_dir+dir_str)
    for file in os.listdir(directory):
        filename = os.fsdecode(file)

        print(dir_str+filename)

        if not any(filename.endswith(ext) for ext in search_exts):
            continue
        f = open(common_dir+dir_str+filename)
        lines = f.readlines()
        f.close()

        #Variable defaults for building parsing
        open_value = []
        currentNode = None
        for i, line in enumerate(lines):
            #Remove comments from line data
            if "#" in line:
                line = line[0:line.find("#")]
            #If line is empty (after removing comments) next line
            if line.strip() == "":
                continue
            
            #Turns line into a list of all its elements, which were separated by whitespace (so: ai_weight = { weight = 1 } becomes ["ai_weight", "=", "{", "weight", "=", "1", "}"])
            temp_line_elems = line.strip().split()

            #In case whitespace wasn't used (example line: "ai_weight={weight=1}"), splits into separate elements as expected
            line_elems = []
            for elem in temp_line_elems:
                new_elems = []
                operators = ["{", "}", "=", "<", ">"] #We deal with >= <= later
                if any(operator in elem for operator in operators):
                    new_elems = []
                    elem_str = ""
                    for i in range(len(elem)):
                        if elem[i] in operators:
                            if elem_str != "":
                                new_elems.append(elem_str)
                                elem_str = ""
                            new_elems.append(elem[i])
                        else:
                            elem_str = elem_str+elem[i]
                    if elem_str != "":
                        new_elems.append(elem_str)
                if len(new_elems) > 0:
                    for new_elem in new_elems:
                        line_elems.append(new_elem)
                else:
                    line_elems.append(elem)
            
            #print(json.dumps(line_elems))

            #Now we construct the data structure (linked clausewitzTree nodes) by parsing the clausewitz code's structure
            for i in range(len(line_elems)):
                if line_elems[i] == "}" or line_elems[i] == "{":

                    if line_elems[i] == "}":
                        nextNode = currentNode.parentNode

                    elif line_elems[i] == "{":
                        nextNode = clausewitzTree(open_value[-2],dir_str,currentNode)
                        if currentNode is None:
                            treeList.append(nextNode)
                        else:
                            currentNode.add_child(nextNode)

                        open_value.pop(-1)
                        open_value.pop(-1)

                    if len(open_value) > 0 and currentNode is None:
                        currentNode = clausewitzTree(filename,dir_str,currentNode)
                        currentNode.add_child = nextNode
                    if len(open_value) > 0:
                        valuesList = []
                        op_indices = [i for i, e in enumerate(open_value) if e == "=" or e == ">" or e == "<" ]
                        if len(op_indices) == 0:
                            valuesList = open_value
                        else:
                            for op in reversed(op_indices):
                                if open_value[op-1] == "<" or open_value[op-1] == ">":
                                    open_value[op-1:op+1] = [''.join(open_value[op-1:op+1])]
                                    op = op - 1
                                newValuePair = valuePair(open_value[op-1],open_value[op],open_value[op+1])
                                valuesList.append(newValuePair)
                        for value in valuesList:
                            currentNode.add_child(value)

                    currentNode = nextNode
                    open_value = []
                else:
                    open_value.append(line_elems[i])
            










# Construct usable data structures for our purposes, out of the purely parsed-file data structures just made
buildingList = []
for tree in treeList:
    if tree.nodeType == "buildings\\":
        name = tree.name
        upkeep = []
        produces = []
        for level2 in tree.children:
            if type(level2) is clausewitzTree and level2.name == "resources":
                for level3 in level2.children:
                    if type(level3) is clausewitzTree and level3.name == "upkeep":
                        for level4 in level3.children:
                            upkeep.append(level4)
                    if level3.name == "produces":
                        for level4 in level3.children:
                            produces.append(level4)
        newBuilding = building(name,upkeep,produces)
        buildingList.append(newBuilding)




















# #The first of several iicso mod files this program will need to write
iicso_resource_calc = "event = {\n\
    id = iicso.1000\n\
    is_triggered_only = yes\n\
    hide_window = yes\n\
\n\
    immediate = {\n\
        every_country = {\n\
            limit = {\n\
                OR = {\n\
                    is_country_type = default\n\
                    is_country_type = fallen_empire\n\
                    is_country_type = awakened_fallen_empire\n\
                }\n\
            }\n\
            every_owned_planet = {\n"

for resource in resource_list:
    iicso_resource_calc = iicso_resource_calc+"                set_variable = { which = planet_"+resource+"_output value = 0 }\n"

for buildingInst in buildingList:
    iicso_resource_calc = iicso_resource_calc+"\n\
                if = {\n\
                    limit = { has_building = "+buildingInst.name+" }\n"
    for i in range(15):
        iicso_resource_calc = iicso_resource_calc+"\
                    "+("if " if i == 0 else "} else_if ")
        iicso_resource_calc = iicso_resource_calc+"= { limit = { num_buildings = { type = "+buildingInst.name+" value = "+str(i+1)+" }}\n\
                        set_variable = { which = building_count value = "+str(i+1)+" }\n"
    iicso_resource_calc = iicso_resource_calc+"\
                    }\n\
                    while = {\n\
                        count = building_count\n"
    for upkeepValue in buildingInst.upkeep:
        if type(upkeepValue) is valuePair and upkeepValue.name in resource_list:
            iicso_resource_calc = iicso_resource_calc+"\
                        change_variable = { which = planet_"+upkeepValue.name+"_upkeep value = -"+upkeepValue.value+" }\n"
        elif type(upkeepValue) is clausewitzTree:
            iicso_resource_calc = iicso_resource_calc+upkeepValue.block(6)+"\n"
    for producesValue in buildingInst.produces:
        if type(producesValue) is valuePair and producesValue in resource_list:
            iicso_resource_calc = iicso_resource_calc+"\
                        change_variable = { which = planet_"+producesValue.name+"_output value = "+producesValue.value+" }\n"
        elif type(producesValue) is clausewitzTree:
            iicso_resource_calc = iicso_resource_calc+producesValue.block(6)+"\n"
    iicso_resource_calc = iicso_resource_calc+"\
                    }\n\
                }\n"


f = open(mod_dir+"log.txt","w")
#f.write(iicso_resource_calc)
treeStr = ""
for tree in treeList:
    treeStr = treeStr + tree.block() 
f.write(treeStr)
f.close()