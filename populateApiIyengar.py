__author__ = 'naras_mg'
# libraries
# import matplotlib as plt
from flask import Flask, jsonify, abort, make_response, request
import json, ast, logging, peewee, flask_httpauth, requests
import networkx as nx
from networkx.readwrite import json_graph
import random, string
from datetime import datetime
import copy
import cProfile #, pstats, io
prefix = 'http://api.iyengarlabs.org/v1/'
# own modules
import knowledgeTreeModelSmall as ktm

def entity_json_dict_list(rows):
    rowsDictList = []
    for row in rows:
        db_flds = row.__dict__['__data__']  # get all the db field names/values .. a dictionary
        rowsDictList.append(db_flds)
    return rowsDictList
def addChild_Subject(node_id, rel, title, description='-NA-'):
    relations = {'adhaara': 'ADHAARA_ADHAARI', 'Anga': 'ANGA_ANGI', 'Anonya': 'ANONYA_ASHRAYA',
                 'Ashraya': 'ASHRAYA_ASHREYI', 'Avayavi': 'AVAYAVI', 'darshana': 'DARSHANA',
                 'Dharma': 'DHARMA_DHARMI', 'Janya': 'JANYA_JANAKA', 'Kaarya': 'KAARYA_KAARANA',
                 'Nirupaka': 'NIRUPYA_NIRUPAKA', 'part': 'ANGA',
                 'Prakaara': 'PRAKAARA_PRAKAARI', 'parentchil': 'COMMON_PARENT', 'Uddheshya': 'UDDHESHYA_VIDHEYA',
                 'upa': 'UPAVEDA',
                 'Upabrahmya': 'UPABRAHMYA_UPABRAHMANA', 'upani': 'UPANISHAD', 'Vishaya': 'VISHAYA_VISHAYI'}
    response = requests.post(prefix + 'subject/add',
                             json={'title': title, 'description': description},
                             headers={'parentid': node_id, "relation": relations[rel]})
    if response.status_code in [200, 201]:
        responseAsDict = json.loads(response.text)
        logging.debug('added apiIyengar node: name %s id: %s', title, responseAsDict['subject']['_id'])
    else:
        logging.debug('failed to add apiIyengar under node(subject):%s child: %s status: %i', node_id, title, response.status_code)
        raise ConnectionError('post status:' + str(response.status_code))
    return responseAsDict
def addChild_Work(node_id, rel, title, langcode="Sanskrit", scriptcode="Devanagari", body = '-NA-', hyperlink=''):
    relations = {'adhaara': 'ADHAARA_ADHAARI', 'Anga': 'ANGA_ANGI', 'Anonya': 'ANONYA_ASHRAYA', 'Ashraya': 'ASHRAYA_ASHREYI', 'Avayavi': 'AVAYAVI',
                 'darshana': 'DARSHANA','Dharma': 'DHARMA_DHARMI', 'Janya': 'JANYA_JANAKA', 'Kaarya': 'KAARYA_KAARANA', 'Nirupaka': 'NIRUPYA_NIRUPAKA',
                 'part': 'ANGA', 'Prakaara': 'PRAKAARA_PRAKAARI', 'parentchil': 'COMMON_PARENT', 'Uddheshya': 'UDDHESHYA_VIDHEYA', 'upa': 'UPAVEDA',
                 'Upabrahmya': 'UPABRAHMYA_UPABRAHMANA', 'upani': 'UPANISHAD', 'Vishaya': 'VISHAYA_VISHAYI',
                 'chapter':'CHAPTER', 'commentary':'COMMENTARY', 'subcommentary':'SUB_COMMENTARY', 'comcommentary':'COMMENTARY_ON_COMMENTARY',
                 'derived':'DERIVED', 'partwhole':'PART_WHOLE_RELATION', 'section':'SECTION', 'subsection':'SUB_SECTION', 'volume':'VOLUME'}
    response = requests.post(prefix + 'work/add',
                             json={'title': title, 'tags': [],
                                   "components": [{"type": 'TEXT',
                                                   "langcode": langcode,
                                                   "scriptcode": scriptcode,
                                                   "body": body,
                                                   "hyperlink": hyperlink}]},
                             headers={'parentid': node_id, "relation": relations[rel]})
    if response.status_code in [200, 201]:
        responseAsDict = json.loads(response.text)
        logging.debug('added apiIyengar node: name %s id: %s', title, responseAsDict['subject']['_id'])
    else:
        logging.debug('failed to add apiIyengar under node(subject):%s child: %s status: %i', node_id, title, response.status_code)
        raise ConnectionError('post status:' + str(response.status_code))
    return responseAsDict
def subject_refreshGraph(nodes, edges):
    g = nx.DiGraph()
    for row in nodes:
        g.add_node(row['id'])
        g.nodes[row['id']]['name'] = row['name']
        if 'description' in row: g.nodes[row['id']]['description'] = row['description']
    for row in edges:
        g.add_edge(row['subject1'],row['subject2'])
        g[row['subject1']][row['subject2']]['relation'] = row['relation']
        # if 'sortorder' in row: g[row['subject1']][row['subject2']]['sortorder'] = row['sortorder']
    return g
def work_refreshGraph(nodes, edges):
    g = nx.DiGraph()
    for row in nodes:
        g.add_node(row['id'])
        g.nodes[row['id']]['name'] = row['name']
        if 'components' in row: g.nodes[row['id']]['components'] = row['components']
    for row in edges:
        g.add_edge(row['work1'],row['work2'])
        g[row['work1']][row['work2']]['relation'] = row['relation']
    return g
def subjects_Navigate(g, edges, subjectsDictList, parent_pred_pair, parent):
    for child, rel in edges.items():
        try:
            child_properties = [entry for entry in subjectsDictList if entry['id'] == child][0]
            if parent in parent_pred_pair:
                pred = parent_pred_pair[parent]
                if 'description' not in child_properties: child_properties['description'] = '-NA-'
                pred = addChild_Subject(pred, rel['relation'], child_properties['name'], child_properties['description'])
                parent_pred_pair[child] = pred['subject']['_id']
                if len(g[child]) > 0:
                    nodes_sofar = subjects_Navigate(g, g[child], subjectsDictList, parent_pred_pair, child)
            else: raise IndexError(parent +' not found in ' + parent_pred_pair)
        except ConnectionError as ce:
            print(ce)
        except Exception as e:
            print(e)
def works_Navigate(g, edges, worksDictList, parent_pred_pair, parent):
    for child, rel in edges.items():
        try:
            child_properties = [entry for entry in worksDictList if entry['id'] == child][0]
            if parent in parent_pred_pair:
                pred = parent_pred_pair[parent]
                if 'components' not in child_properties: child_properties['components'] = '-NA-'
                pred = addChild_Work(pred, rel['relation'], child_properties['name'], child_properties['components'])
                parent_pred_pair[child] = pred['subject']['_id']
                if len(g[child]) > 0:
                    works_Navigate(g, g[child], worksDictList, parent_pred_pair, child)
            else: raise IndexError(parent +' not found in ' + parent_pred_pair)
        except ConnectionError as ce:
            print(ce)
        except Exception as e:
            print(e)

def main():
    logging.basicConfig(filename='populateApiIyengarJournal.log',format='%(asctime)s %(message)s',level=logging.DEBUG)

    db = ktm.database
    db.create_tables([ktm.Subject, ktm.SubjectSubjectRelation, ktm.SubjectRelatestoSubject, \
                      ktm.Work, ktm.WorkWorkRelation, ktm.WorkRelatestoWork, \
                      ktm.SubjectHasWork, ktm.WorkSubjectRelation], safe=True)
    logging.debug('Opened knowledgeTree Tables - Subject, SubjectSubjectRelation, Subject-Relates-to-Subject, Work, WorkWorkRelation Work_Relatesto_Work, SubjectHasWork % WorkSubjectRelation')


    # subject related entities
    srs = ktm.SubjectRelatestoSubject.select()
    srsDictList = entity_json_dict_list(srs)
    subjects = ktm.Subject.select()
    subjectsDictList = entity_json_dict_list(subjects)

    # work related entities
    wrw = ktm.WorkRelatestoWork.select()
    wrwDictList = entity_json_dict_list(wrw)
    works = ktm.Work.select()
    worksDictList = entity_json_dict_list(works)

    # logging.debug('populated Subject, Work, Person  and related in-memory tables')

    gs = subject_refreshGraph(subjectsDictList, srsDictList)
    parent = 'aum'
    parent_pred_pair = {'aum':'1001'}
    subjects_Navigate(gs, gs['aum'], subjectsDictList, parent_pred_pair, parent)
    gw = work_refreshGraph(worksDictList, wrwDictList)
    parent = 'all'
    parent_pred_pair = {'all':'1001'}
    works_Navigate(gw, gw['all'], worksDictList, parent_pred_pair, parent)


if __name__ == '__main__':
    main()
