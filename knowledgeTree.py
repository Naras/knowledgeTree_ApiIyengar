from flask import Flask, jsonify, abort, make_response, request
import json, ast, logging, requests
import networkx as nx
from networkx.readwrite import json_graph
import random, string
from datetime import datetime
import matplotlib as plt

prefix = 'http://api.iyengarlabs.org/v1/'
endpoint_prefix = '/knowledgeTree/api/v1.0/'
logging.basicConfig(filename='knowledgeTreeJournal.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
app = Flask(__name__)

def find_item_json_dict_list(lst,key,value):
    for dic in lst:
        # print dic, type(dic)
        if dic[key] == value: return dic
    return None
def entity_json_dict_list(rows):
    rowsJson = []
    for row in rows:
        jsonElement = '{'
        for fld_name,fld_value in row.items():
            if not fld_value is None:
                # print ('name:'+fld_name + ' value:'+fld_value)
                withoutCRLF = str(fld_value).replace('\r\n','')
                withoutCRLF = withoutCRLF.replace('\n','')
                withoutCRLF = withoutCRLF.replace("'", r'\"')
                # if fld_name == 'description':
                #     logging.debug(auth.username() + withoutCRLF)
                jsonElement += "'" + fld_name + "':'" + withoutCRLF + "',"  # escape /r/n
        elem = jsonElement[:-1] + '}'
        # elem = ast.literal_eval(jsonElement2)
        # print elem
        rowsJson.append(ast.literal_eval(elem))
    return rowsJson
def subject_refreshGraph():
    g = nx.Graph()
    for row in subjects:
        g.add_node(row['id'])
        g.nodes[row['id']]['name'] = row['title']
        if 'description' in row: g.nodes[row['id']]['description'] = row['description']
    for row in srs:
        g.add_edge(row['subject1'],row['subject2'])
        g[row['subject1']][row['subject2']]['relation'] = row['relation']
        if 'sortorder' in row: g[row['subject1']][row['subject2']]['sortorder'] = row['sortorder']
    return g
# def work_refreshGraph():
#     g = nx.Graph()
#     for row in worksJson:
#         g.add_node(row['id'])
#         g.node[row['id']]['name'] = row['name']
#         if 'description' in row: g.node[row['id']]['description'] = row['description']
#     for row in wrwJson:
#         g.add_edge(row['work1'],row['work2'])
#         g[row['work1']][row['work2']]['relation'] = row['relation']
#         if 'sortorder' in row:
#             g[row['work1']][row['work2']]['sortorder'] = row['sortorder']
#             # print row['sortorder']
#         else:g[row['work1']][row['work2']]['sortorder'] = '99'
#         # print g[row['work1']][row['work2']]
#     return g
def add_name_description(td):
    for child in td['children']:
        child['name'] = gs.nodes[child['id']]['name']
        child['description'] = gs.nodes[child['id']]['description']
        for row in srs:
            if child['id'] == row['subject2']:
                child['parent'] = row['subject1']
                child['relation'] = row['relation']
                break
        if 'children' in child:
            child = add_name_description(child)
    # print(td)
    return td
def getChildren_Subject(subject_relations):
    for entry in subject_relations:
        if entry['subjecttype'] not in ssr:
            raise KeyError('Invalid relation')
        Request_Url_child = entry['_links']['self']['href']
        if str(Request_Url_child).startswith('/v1'): Request_Url_child = prefix + Request_Url_child[4:]
        response = requests.get(Request_Url_child)
        if response.status_code == 200:
            responseAsDict = json.loads(response.text)
            if 'subject_relations' in responseAsDict['subject']:
                # has child nodes/subtree
                subjects.append({'id':responseAsDict['subject']['_id'], 'title':responseAsDict['subject']['title'], 'description':responseAsDict['subject']['description']})
                for item in responseAsDict['subject']['subject_relations']:
                    srs.append({'subject1':responseAsDict['subject']['subject_parents'][0]['id'], 'subject2':responseAsDict['subject']['_id'],'relation':item['subjecttype']})
                getChildren_Subject(responseAsDict['subject']['subject_relations'])
            else:
                # leaf node
                subjects.append({'id':responseAsDict['subject']['_id'], 'title':responseAsDict['subject']['title'], 'description':responseAsDict['subject']['description']})
def getChildren_Work(self, work_relations):
        for entry in work_relations:
            self.assertIn(entry['worktype'], wwr)
            Request_Url_child = entry['_links']['self']['href']
            if str(Request_Url_child).startswith('/v1'): Request_Url_child = prefix + Request_Url_child
            response = requests.get(Request_Url_child)
            if response.status_code == 200:
                responseAsDict = json.loads(response.text)
                # for k,v in responseAsDict['work'].items(): print('k:%s v:%s'%(k,v))
                node = responseAsDict['work']['_id']
                if 'work_relations' in responseAsDict['work']:
                    # has child nodes/subtree
                    print('non-leaf node id:%s title:%s parent:%s\ncomponents:%s\nchild exists - relation:%s id:%s' %
                          (responseAsDict['work']['_id'], responseAsDict['work']['title'],
                           responseAsDict['work']['work_parents'][0]['id'],
                           responseAsDict['work']['components'],
                           responseAsDict['work']['work_relations'][0]['worktype'],
                           responseAsDict['work']['work_relations'][0]['id']))
                    getChildren_Work(self, responseAsDict['work']['work_relations'])
                else:
                    # leaf node
                    print('leaf node id:%s title:%s parent:%s\ncomponents:%s' %
                          (responseAsDict['work']['_id'], responseAsDict['work']['title'],
                           responseAsDict['work']['work_parents'][0]['id'],
                           responseAsDict['work']['components']))

                self.assertIn('title', responseAsDict['work'])
                self.assertIn('work_parents', responseAsDict['work'])

ssr = ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'DARSHANA',
       'DHARMA_DHARMI', 'JANYA_JANAKA', 'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA', 'ANGA', 'PRAKAARA_PRAKAARI',
       'COMMON_PARENT',
       'UDDHESHYA_VIDHEYA', 'UPAVEDA', 'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI']
response = requests.get(prefix + 'rootsubject')
responseAsDict = json.loads(response.text)
if 'subject_relations' in responseAsDict['subject']:
    subject_relations = responseAsDict['subject']['subject_relations']
# subject related entities
subjects, srs = [], []
getChildren_Subject(subject_relations)
# srsJson = json.dumps(srs)
# subjectsJson = json.dumps(subjects)
# print(subjects==subjectsJson)
wwr = ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'CHAPTER',
                           'COMMENTARY_ON_COMMENTARY', 'COMMENTARY',
                           'DARSHANA', 'DERIVED', 'DHARMA_DHARMI', 'JANYA_JANAKA', 'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA',
                           'ORIGINAL', 'ANGA',
                           'PART_WHOLE_RELATION', 'PRAKAARA_PRAKAARI', 'REVIEW', 'SECTION', 'COMMON_PARENT',
                           'SUB_COMMENTARY', 'SUB_SECTION', 'UDDHESHYA_VIDHEYA',
                           'UPAVEDA', 'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI', 'VOLUME']
# work related entities
works, wrw = [], []
# response = requests.get(prefix + 'rootwork')
# responseAsDict = json.loads(response.text)
# if 'work_relations' in responseAsDict['work']:
#     work_relations = responseAsDict['work']['work_relations']
# getChildren_Work(work_relations)
# print(works)
# wwrJson = entity_json_dict_list(wwr)
# wrwJson = entity_json_dict_list(wrw)

# worksJson = entity_json_dict_list(works)

gs = subject_refreshGraph()
# gw = work_refreshGraph()
# nx.draw(gs)
# plt.pyplot.show()
@app.route(endpoint_prefix + 'tree', methods=['GET'])
def get_tree():
    logging.debug(':servicing JSON GET tree')
    return jsonify(add_name_description(json_graph.tree_data(nx.bfs_tree(gs, '1001'),"1001")))

if __name__ == '__main__':
    app.run(debug=True)