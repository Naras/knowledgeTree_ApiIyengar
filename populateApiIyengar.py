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

def find_item_json_dict_list(lst,key,value):
    for dic in lst:
        # print dic, type(dic)
        if dic[key] == value: return dic
    return None
def entity_json_dict_list(rows):
    rowsJson = []
    for row in rows:
        db_flds = row.__dict__['__data__']  # get all the db field names/values .. a dictionary
        jsonElement = '{'
        for fld_name,fld_value in db_flds.items():
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
        # created_id_child = responseAsDict['subject']['_id']
        logging.debug('added apiIyengar node:', responseAsDict)
        # self.assertIn('title', responseAsDict['subject'])
        # self.assertEqual(title, responseAsDict['subject']['title'])
        # self.assertIn('description', responseAsDict['subject'])
        # self.assertEqual(description, responseAsDict['subject']['description'])
        # self.assertIn('id', responseAsDict['subject']['subject_parents'][0])
        # self.assertEqual(node_id, responseAsDict['subject']['subject_parents'][0]['id'])
        # response = requests.get(prefix + 'subject/' + node_id)
        # self.assertIn(response.status_code, [200, 201])
    else:
        logging.debug('failed to add apiIyengar under node(subject):' + node_id + ' child:' + title + ' status:' + str(response.status_code))
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
        created_id_child = responseAsDict['work']['_id']
        logging.debug('added apiIyengar node(work):', responseAsDict)
        # self.assertIn('title', responseAsDict['work'])
        # self.assertEqual('child-' + node['title'], responseAsDict['work']['title'])
        # self.assertIn('components', responseAsDict['work'])
        # self.assertEqual([{"type": 'TEXT', "langcode": "Sanskrit", "scriptcode": "Devanagari",
        #                    "body": "blah witter drone this is the greatest long work since the moon landing",
        #                    "hyperlink": "https://en.wikipedia.org/wiki/Nakshatra"}], responseAsDict['work']['components'])
        # self.assertIn('id', responseAsDict['work']['work_parents'][0])
        # self.assertEqual(node['_id'], responseAsDict['work']['work_parents'][0]['id'])
        # response = requests.get(prefix + 'work/' + node['_id'])
        # self.assertIn(response.status_code, [200, 201])
        # responseAsDict = json.loads(response.text)
        # print('node after:', responseAsDict)
    else:
        logging.debug('failed to add apiIyengar under node(work):' + node_id + ' child:' + title + ' status:' + str(response.status_code))
        raise ConnectionError('post status:' + str(response.status_code))
    return responseAsDict

logging.basicConfig(filename='populateApiIyengarJournal.log',format='%(asctime)s %(message)s',level=logging.DEBUG)

app = Flask(__name__)

db = ktm.database
db.create_tables([ktm.Subject, ktm.SubjectSubjectRelation, ktm.SubjectRelatestoSubject, \
                  ktm.Work, ktm.WorkWorkRelation, ktm.WorkRelatestoWork, \
                  ktm.SubjectHasWork, ktm.WorkSubjectRelation], safe=True)
logging.debug('Opened knowledgeTree Tables - Subject, SubjectSubjectRelation, Subject-Relates-to-Subject, Work, WorkWorkRelation Work_Relatesto_Work, SubjectHasWork % WorkSubjectRelation')


# subject related entities
ssr = ktm.SubjectSubjectRelation.select()
ssrJson = entity_json_dict_list(ssr)
srs = ktm.SubjectRelatestoSubject.select()
srsJson = entity_json_dict_list(srs)
subjects = ktm.Subject.select()
subjectsJson = entity_json_dict_list(subjects)

# work related entities
wwr = ktm.WorkWorkRelation.select()
wwrJson = entity_json_dict_list(wwr)
wrw = ktm.WorkRelatestoWork.select()
wrwJson = entity_json_dict_list(wrw)
works = ktm.Work.select()
worksJson = entity_json_dict_list(works)

# subject-work cross related entities
wsr = ktm.WorkSubjectRelation.select()
wsrJson = entity_json_dict_list(wsr)
shw = ktm.SubjectHasWork.select()
shwJson= entity_json_dict_list(shw)

# person related entities
ppr = ktm.PersonPersonRelation.select()
pprJson = entity_json_dict_list(ppr)
prp = ktm.PersonRelatestoPerson.select()
prpJson = entity_json_dict_list(prp)
persons = ktm.Person.select()
personsJson = entity_json_dict_list(persons)

# person-work cross related entities
pwr = ktm.PersonWorkRelation.select()
pwrJson = entity_json_dict_list(pwr)
phw = ktm.PersonHasWork.select()
phwJson= entity_json_dict_list(phw)

# logging.debug('populated Subject, Work, Person  and related in-memory tables')

# print(gs.nodes)
# print(gs.nodes(data=True)['aum'])
parent_pred_pair = {'all':'1001'}
for srsEntry in srsJson:
    parent, child = srsEntry['subject1'], srsEntry['subject2'] #nx.predecessor(gs, node, cutoff=1)
    try:
        child_properties = [entry for entry in subjectsJson if entry['id'] == child][0]  # eq. sql select from subjects where subject2=id
        if parent in parent_pred_pair.keys():
            pred = parent_pred_pair[parent]
        else:
            parent, pred = 'all', '1001'
        if 'description' in child_properties:
            print(pred, '->', child_properties['name'], child_properties['description'], srsEntry['relation'])
            pred = addChild_Subject(pred, srsEntry['relation'], child_properties['name'], child_properties['description'])
        else:
            print(pred, '->', child_properties['name'], '-NA-', srsEntry['relation'])
            pred = addChild_Subject(pred, srsEntry['relation'], child_properties['name'])
        parent_pred_pair[child] = pred['subject']['_id']
    except ConnectionError as ce:
        print(ce)
    except Exception as e:
        print(e)

parent_pred_pair = {'all':'1001'}
for wrwEntry in wrwJson:
    parent, child = wrwEntry['work1'], wrwEntry['work2']
    try:
        child_properties = [entry for entry in worksJson if entry['id'] == child][0]
        # print('pair:%s\nchild:%s properties:%s'%(parent_pred_pair,child,child_properties))
        if parent in parent_pred_pair.keys():
            pred = parent_pred_pair[parent]
        else:
            parent, pred = 'all', '1001'
        if 'description' in child_properties:
            print(pred, '->', child_properties['name'], child_properties['description'], wrwEntry['relation'])
            pred = addChild_Work(pred, wrwEntry['relation'], child_properties['name'], body=child_properties['description'])
        else:
            print(pred, '->', child_properties['name'], '-NA-', wrwEntry['relation'])
            pred = addChild_Work(pred, wrwEntry['relation'], child_properties['name'])
        parent_pred_pair[child] = pred['work']['_id']
    except ConnectionError as ce:
        print(ce)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    app.run(debug=True)