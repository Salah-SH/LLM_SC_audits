# LLM_SC_audits

**this is the dataset used for experiments in the paper** [Co-Auditing Smart Contracts](https://arxiv.org/abs/2406.18075)

**prerequist** : [slither](https://github.com/crytic/slither) installed

generate call graph from smart contract : 
```
   chmod +x functionCall.sh
   ./functionCall.sh $path_to_smartContract
```
In the script call_graph.py, at line 12, insert the name of the smart contract to create the Function Call code list for it.

     
