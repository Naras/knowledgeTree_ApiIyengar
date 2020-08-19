from flask import Flask, jsonify #, abort, make_response, request
import json, logging, requests
import networkx as nx
from networkx.readwrite import json_graph
# from datetime import datetime
# import matplotlib as plt

prefix = 'http://api.iyengarlabs.org/v1/'
endpoint_prefix = '/knowledgeTree/api/v1.0/'
logging.basicConfig(filename='knowledgeTreeJournal.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
app = Flask(__name__)

def subject_refreshGraph(nodes, edges):
    g = nx.Graph()
    # g.add_nodes_from(nodes)
    # g.add_edges_from(edges)
    for row in nodes:
        g.add_node(row['id'])
        g.nodes[row['id']]['name'] = row['title']
        if 'description' in row: g.nodes[row['id']]['description'] = row['description']
    for row in edges:
        g.add_edge(row['subject1'],row['subject2'])
        g[row['subject1']][row['subject2']]['relation'] = row['relation']
        # if 'sortorder' in row: g[row['subject1']][row['subject2']]['sortorder'] = row['sortorder']
    return g
def work_refreshGraph(nodes, edges):
    g = nx.Graph()
    for row in nodes:
        g.add_node(row['id'])
        g.nodes[row['id']]['name'] = row['title']
        if 'components' in row: g.nodes[row['id']]['components'] = row['components']
    for row in edges:
        g.add_edge(row['work1'],row['work2'])
        g[row['work1']][row['work2']]['relation'] = row['relation']
    return g
def add_name_description(td, g):
    for dict in g.nodes(data=True):
        if td['id'] == dict[0]: break
    td['name'] = dict[1]['name']
    if 'description' in dict[1]: td['description'] = dict[1]['description']
    for row in g.edges(data=True):
        if td['id'] == row[0]:
            td['parent'] = row[1]
            td['relation'] = row[2]['relation']
            break
    if 'children' in td:
        for child in td['children']:
            child = add_name_description(child, g)
    return td
def getChildren_Subject(subject, g):
    # if not subject['_id'] == '1001': print(subject['subject_parents'][0]['id'], subject['_id'], subject['title'])
    g.nodes[subject['_id']]['name'] = subject['title']
    g.nodes[subject['_id']]['description'] = subject['description']
    if 'subject_relations' in subject:
        for entry in subject['subject_relations']:
            if entry['subjecttype'] not in ssr: raise KeyError('Invalid relation')
            if not g.has_node(entry['id']):
                g.add_node(entry['id'])
                g.add_edge(subject['_id'],entry['id'])
                g[subject['_id']][entry['id']]['relation'] = entry['subjecttype']
                Request_Url_child = prefix + 'subject/' + entry['id'] #entry['_links']['self']['href']
                response = requests.get(Request_Url_child)
                if response.status_code == 200:
                    responseAsDict = json.loads(response.text)
                    g = getChildren_Subject(responseAsDict['subject'], g)
    return g
def add_name_description_work(td, g):
    for dict in g.nodes(data=True):
        if td['id'] == dict[0]: break
    td['name'] = dict[1]['name']
    if 'components' in dict[1]: td['components'] = dict[1]['components']
    for row in g.edges(data=True):
        if td['id'] == row[0]:
            td['parent'] = row[1]
            td['relation'] = row[2]['relation']
            break
    if 'children' in td:
        for child in td['children']:
            child = add_name_description_work(child, g)
    return td
def getChildren_Work(work, g):
    # if not work['_id'] == '1001': print(work['work_parents'][0]['id'], work['_id'], work['title'])
    g.nodes[work['_id']]['name'] = work['title']
    if 'components' in work: g.nodes[work['_id']]['components'] = work['components']
    if 'work_relations' in work:
     for entry in work['work_relations']:
        if entry['worktype'] not in wwr: raise KeyError('Invalid relation')
        g.add_node(entry['id'])
        g.add_edge(work['_id'],entry['id'])
        g[work['_id']][entry['id']]['relation'] = entry['worktype']
        Request_Url_child =  prefix + 'work/' + entry['id'] #entry['_links']['self']['href']
        response = requests.get(Request_Url_child)
        if response.status_code == 200:
            responseAsDict = json.loads(response.text)
            getChildren_Work(responseAsDict['work'], g)
    return g

ssr = ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'DARSHANA',
       'DHARMA_DHARMI', 'JANYA_JANAKA', 'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA', 'ANGA', 'PRAKAARA_PRAKAARI',
       'COMMON_PARENT', 'UDDHESHYA_VIDHEYA', 'UPAVEDA', 'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI']
response = requests.get(prefix + 'rootsubject')
responseAsDict = json.loads(response.text)
gs = nx.DiGraph()
subject = responseAsDict['subject']
gs.add_node(subject['_id'])
gs.nodes[subject['_id']]['name'] = subject['title']
gs = getChildren_Subject(subject, gs)
wwr = ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'CHAPTER',
                           'COMMENTARY_ON_COMMENTARY', 'COMMENTARY',
                           'DARSHANA', 'DERIVED', 'DHARMA_DHARMI', 'JANYA_JANAKA', 'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA',
                           'ORIGINAL', 'ANGA',
                           'PART_WHOLE_RELATION', 'PRAKAARA_PRAKAARI', 'REVIEW', 'SECTION', 'COMMON_PARENT',
                           'SUB_COMMENTARY', 'SUB_SECTION', 'UDDHESHYA_VIDHEYA',
                           'UPAVEDA', 'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI', 'VOLUME']
# work related entities
response = requests.get(prefix + 'rootwork')
responseAsDict = json.loads(response.text)
gw = nx.DiGraph()
work = responseAsDict['work']
gw.add_node(work['_id'])
gw.nodes[work['_id']]['name'] = work['title']
gw = getChildren_Work(work, gw)
@app.route(endpoint_prefix + 'tree', methods=['GET'])
def get_tree():
    logging.debug(':servicing JSON GET subject tree')
    # data = json_graph.tree_data(nx.bfs_tree(gs, '1001'),'1001')
    # json.dump(data, open('jsondata/tree-subject.json','w'))
    return jsonify(add_name_description(json_graph.tree_data(nx.bfs_tree(gs, '1001'),'1001'), gs))
@app.route(endpoint_prefix + 'tree-work', methods=['GET'])
def get_tree_work():
    logging.debug(':servicing JSON GET work tree')
    # data = json_graph.tree_data(nx.bfs_tree(gw, '1001'),'1001')
    # json.dump(data, open('jsondata/tree-work.json','w'))
    return jsonify(add_name_description_work(json_graph.tree_data(nx.bfs_tree(gw, '1001'),'1001'), gw))

if __name__ == '__main__':
    app.run(debug=True)