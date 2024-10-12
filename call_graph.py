import pydot
import networkx as nx
import os
#import sys
import fnmatch
import csv
import pandas as pd
import re

####input the smart contract file name
filenameroot=sys.argv[0]
# filenameroot=f"40.sol"

dot_graph = pydot.graph_from_dot_file(f"{filenameroot}.all_contracts.call-graph.dot")[0]
contract_names = []
contract_nums=[]
functions_id = []
All_edges = {}


for subgraph in dot_graph.get_subgraphs() :

    subgraph_name=subgraph.get_name()
    contract_nums.append(subgraph_name.split("_")[1])
    contract_names.append(subgraph_name.split("_")[-1])
    contract_label=dict(zip(contract_nums,contract_names))
    
    
    for edge in subgraph.get_edges():
        edge_source = edge.get_source().split("_",1)[1][:-1]
        edge_source_num=edge.get_source().split("_")[0][1:]
        edge_source_contract=contract_label[edge_source_num]

        edge_destination = edge.get_destination().split("_")
        
        
        if len(edge_destination)>1 :
            edge_destination = edge.get_destination().split("_",1)[-1][:-1]
            edge_destination_num = edge.get_destination().split("_")[0][1:]
            edge_destination_contract=contract_label[edge_destination_num]

            edge = {(edge_source_contract, edge_source):(edge_destination_contract,edge_destination)}
            All_edges.update(edge)



#--------------------------------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------------------------------------#
#from the original code, find all contracts, and all functions#

from slither.slither import Slither
contract_from_slither=Slither(f"{filenameroot}").contracts


all_contracts=[]
all_functions=[]


for contract in contract_from_slither:
    all_contracts.append(contract)

    contract_functions=[]
    for function in contract.functions:
        #if contract.name == "Party" or contract.name == "PartyGovernanceNFT" or contract.name == "PartyGovernance" or contract.name == "ERC721" or contract.name == "IERC2981" or contract.name == "ERC721TokenReceiver" or contract.name == "ReadOnlyDelegateCall" or contract.name == "ERC1155Receiver" or contract.name == "ProposalStorage" or contract.name == "IERC165":
          #  all_functions.append(("",function.name))
        #else:
        all_functions.append((contract.name,function.name))
all_functions=list(set(all_functions))
#----------------------------------------------------------------------------------------------------------------#
#create a call list
class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rootX = self.find(x)
        rootY = self.find(y)

        if rootX == rootY:
            return

        if self.rank[rootX] > self.rank[rootY]:
            self.parent[rootY] = rootX
        else:
            self.parent[rootX] = rootY
            if self.rank[rootX] == self.rank[rootY]:
                self.rank[rootY] += 1

def group_sublists(lst):
    uf = UnionFind()

    # Step 2: Union elements from sublists with common elements
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            for elem in lst[i]:
                if elem in lst[j]:
                    uf.union(lst[i][0], lst[j][0])
                    break

    # Step 3: Group by the representative element
    groups = {}
    for sublist in lst:
        root = uf.find(sublist[0])
        if root not in groups:
            groups[root] = set()
        for elem in sublist:
            groups[root].add(elem)

    # Step 4: Output the grouped results
    result = [list(group) for group in groups.values()]

    return result

def generate_call_code_list(functions, call_graph):
    call_code_list_all=[]
    def dfs(function):
        if function not in call_code_list:
            call_code_list.append(function)
            if function in call_graph:
                dfs(call_graph[function])

        return call_code_list
    for function in functions:
        call_code_list = []
        call_code_list_all.append(dfs(function))
    return call_code_list_all

call_list=generate_call_code_list(all_functions,All_edges)

call_list=call_list


call_list=group_sublists(call_list)



#------------------------------------code list-----------------------------------
# create a code list

code=""

sol_files_content = {}


with open(f"{filenameroot}", 'r') as f:
    code=f.read()

#code_files = [f for f in os.listdir("./crytic-export/codeonly") if f.endswith('.sol')]
#for sol_file in code_files:
 #   with open(f"./crytic-export/codeonly/{sol_file}", 'r') as f:
  #      sol_files_content[sol_file] = f.read()
   #     print(type(sol_files_content[sol_file]))
    #    code=code+sol_files_content[sol_file]


def remove_comments(input_string):
    pattern = r"//.*"
    output_string = re.sub(pattern, "", input_string, flags=re.MULTILINE)
    return output_string

code=remove_comments(code)

with open('code.txt', 'w') as f:
    f.write(code)

#-----confirm the starting line
def extract_contract_lines_procedure(text,title,keyword):
    lines = text.split('\n')
    keyword_line = None
    keywordnew=title+keyword
    for i, line in enumerate(lines):
        if keywordnew in line:
            keyword_line = i
            break
    if keyword_line != None:
        lines = lines[keyword_line:] 
        extracted_text = '\n'.join(lines) 
        return extracted_text
    return None


def extract_contract_lines(text, keyword):
    contract_texts = [
        extract_contract_lines_procedure(text, "contract ", keyword),
        extract_contract_lines_procedure(text, "library ", keyword),
        extract_contract_lines_procedure(text, "interface ", keyword),
        extract_contract_lines_procedure(text, "abstract contract ", keyword)
    ]
    for contract_text in contract_texts:
        if contract_text:
            return contract_text
    return None
        
def extract_function_lines_procedure(text, title, keyword):
    lines = text.split('\n')  
    keyword_line = None
    keyword_func = title + keyword
    for i, line in enumerate(lines):
        if keyword_func in line:
            keyword_line = i
            break
    if keyword_line is not None:
        # If the function is a single-line definition (i.e., it ends with a semicolon)
        if ";" in lines[keyword_line]:
            return lines[keyword_line]
        else:  # Else, it's a multi-line function definition
            closing_brace_found = False
            for j, subsequent_line in enumerate(lines[keyword_line:]):
                if "}" in subsequent_line:
                    closing_brace_found = True
                    break
            if closing_brace_found:
                return '\n'.join(lines[keyword_line: keyword_line + j + 1])
    else:
        return None
    
    
def extract_function_lines(contract_code, keyword):
    for prefix in ["function ", "event ", "constructor ","modifier "]:
        result = extract_function_lines_procedure(contract_code, prefix, keyword)
        if result:
            return result
    return None


#----------confirm the ending line
def extract_function_code(code: str) -> str:
    opening_brace_count = 0
    closing_brace_count = 0
    function_code = ""
    match_found = False

    for char in code:
        if char == '{':
            opening_brace_count += 1
            if match_found:
                function_code += char
        elif (char != '{') and (char != '}'):
            function_code+=char
        elif char == '}':
            closing_brace_count += 1
            if match_found:
                function_code += char
            if opening_brace_count > 0 and opening_brace_count == closing_brace_count:
                break

        if opening_brace_count == 1 and not match_found:
            match_found = True
            function_code += char

    return function_code.strip()


#--------------confirm a code
def find_code(contract_name,function_name,code):
        contract_code=extract_contract_lines(code,contract_name)
        if contract_code!=None:
            function_start=extract_function_lines(contract_code,function_name)
            if (function_start!=None) and (len(function_start)>1):
                function_code=extract_function_code(function_start)
                return function_code
            elif (function_start==None):
                return (contract_name+" does not have this function: "+ function_name)
            else:
                return function_start
        else:
            return("Does not have this contract: "+contract_name)

call_code_all=[]

for calls in call_list:
    call_code=[]
    for i in range(len(calls)):
        if calls[i][1]!="fallback":
            call_code.append(find_code(calls[i][0],calls[i][1],code))
        else:
            call_code.append(find_code(calls[i][0],"",code))
    call_code_all.append(call_code)





