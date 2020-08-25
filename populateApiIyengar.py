__author__ = 'naras_mg'
# libraries
# import matplotlib as plt
import json, logging, requests
import networkx as nx
prefix = 'http://api.iyengarlabs.org/v1/'
# own modules
import knowledgeTreeModelSmall as ktm

def entity_json_dict_list(rows):
    rowsDictList = []
    for row in rows:
        db_flds = row.__dict__['__data__']  # get all the db field names/values .. a dictionary
        rowsDictList.append(db_flds)
    return rowsDictList
def addChild(node_id, rel, entity, jsonFields, valid_relations):
    response = requests.post(prefix + entity + '/add', json=jsonFields, headers={'parentid': node_id, 'relation': valid_relations[rel]})
    name_title = 'title' if entity in ['subject', 'work'] else 'name'
    if response.status_code in [200, 201]:
        responseAsDict = json.loads(response.text)
        logging.debug('added apiIyengar node: name %s id: %s parent %s', jsonFields[name_title], responseAsDict[entity]['_id'], node_id)
    else:
        logging.debug('failed to add apiIyengar under %s node:%s child: %s status: %i', entity, node_id, json[name_title], response.status_code)
        raise ConnectionError('post status:' + str(response.status_code))
    return responseAsDict
def refreshGraph(nodes, edges, entity='subject'):
    g = nx.DiGraph()
    for row in nodes:
        g.add_node(row['id'])
        if entity == 'subject':
            g.nodes[row['id']]['name'] = row['name']
            if 'description' in row: g.nodes[row['id']]['description'] = row['description']
        elif entity=='work':
            g.nodes[row['id']]['name'] = row['name']
            if 'components' in row: g.nodes[row['id']]['components'] = row['components']
        else:  # entity=='person':
            if 'first' in row: g.nodes[row['id']]['name'] = row['first']
            if 'middle' in row and not row['middle']==None: g.nodes[row['id']]['name'] += ' ' + row['middle']
            if 'last' in row and not row['last']==None: g.nodes[row['id']]['name'] += ' ' + row['last']
            if 'birth' in row: g.nodes[row['id']]['birth'] = row['birth']
            if 'death' in row: g.nodes[row['id']]['birth'] = row['birth']
            if 'biography' in row: g.nodes[row['id']]['biography'] = row['biography']

    for row in edges:
        g.add_edge(row[entity + '1'],row[entity + '2'])
        g[row[entity + '1']][row[entity + '2']]['relation'] = row['relation']
        # if 'sortorder' in row: g[row['subject1']][row['subject2']]['sortorder'] = row['sortorder']
    return g
def tree_Navigate(g, edges, dictList, parent_pred_pair, parent, entity='subject'):
    dependant_structures = {'subject':{'other':'description', 'valid_relations':
        {'adhaara': 'ADHAARA_ADHAARI', 'Anga': 'ANGA_ANGI', 'Anonya': 'ANONYA_ASHRAYA', 'Ashraya': 'ASHRAYA_ASHREYI', 'Avayavi': 'AVAYAVI',
         'darshana': 'DARSHANA', 'Dharma': 'DHARMA_DHARMI', 'Janya': 'JANYA_JANAKA', 'Kaarya': 'KAARYA_KAARANA', 'Nirupaka': 'NIRUPYA_NIRUPAKA',
         'part': 'ANGA', 'Prakaara': 'PRAKAARA_PRAKAARI', 'parentchil': 'COMMON_PARENT', 'Uddheshya': 'UDDHESHYA_VIDHEYA', 'upa': 'UPAVEDA',
         'Upabrahmya': 'UPABRAHMYA_UPABRAHMANA','upani': 'UPANISHAD', 'Vishaya': 'VISHAYA_VISHAYI'}},
        'work':{'other':'components', 'valid_relations':
            {'adhaara': 'ADHAARA_ADHAARI', 'Anga': 'ANGA_ANGI', 'Anonya': 'ANONYA_ASHRAYA', 'Ashraya': 'ASHRAYA_ASHREYI', 'Avayavi': 'AVAYAVI',
             'darshana': 'DARSHANA', 'Dharma': 'DHARMA_DHARMI', 'Janya': 'JANYA_JANAKA', 'Kaarya': 'KAARYA_KAARANA', 'Nirupaka': 'NIRUPYA_NIRUPAKA',
             'part': 'ANGA', 'Prakaara': 'PRAKAARA_PRAKAARI', 'parentchil': 'COMMON_PARENT', 'Uddheshya': 'UDDHESHYA_VIDHEYA', 'upa': 'UPAVEDA',
             'Upabrahmya': 'UPABRAHMYA_UPABRAHMANA', 'upani': 'UPANISHAD', 'Vishaya': 'VISHAYA_VISHAYI', 'chapter': 'CHAPTER',
             'commentary': 'COMMENTARY', 'subcommentary': 'SUB_COMMENTARY', 'comcommentary': 'COMMENTARY_ON_COMMENTARY', 'derived': 'DERIVED',
             'partwhole': 'PART_WHOLE_RELATION', 'section': 'SECTION', 'subsection': 'SUB_SECTION', 'volume': 'VOLUME'}},
        'person':{'other':None, 'valid_relations':{'gurushishya':'GURISHISHYA', 'classmate':'CONTEMPORARY'}}}
    valid_relations = dependant_structures[entity]['valid_relations']
    for child, rel in edges.items():
        try:
            child_properties = [entry for entry in dictList if entry['id'] == child][0]
            if parent in parent_pred_pair:
                pred = parent_pred_pair[parent]
                jsonFields = {'subject':{'title': getIfExists(child_properties,'name'), 'description': getIfExists(child_properties,'description')},
                'work':{'title': getIfExists(child_properties,'name'), 'tags':[], 'components':[{'type': 'TEXT', 'langcode': 'Sanskrit',
                                             'scriptcode': 'Devanagari','body': getIfExists(child_properties,'description'), 'hyperlink': ''}]},
                'person':{'name': getIfExists(child_properties, 'first') + getIfExists(child_properties, 'middle') + getIfExists(child_properties, 'last'),
                          'biography': getIfExists(child_properties, 'biography')}}[entity]
                # print(jsonFields)
                pred = addChild(pred, rel['relation'], entity, jsonFields, valid_relations)
                parent_pred_pair[child] = pred[entity]['_id']
                if len(g[child]) > 0:
                    tree_Navigate(g, g[child], dictList, parent_pred_pair, child, entity)
            else: raise IndexError(parent +' not found in ' + parent_pred_pair)
        except ConnectionError as ce:
            print(ce)
        except Exception as e:
            print(e)
def getIfExists(dict, key):
    return dict[key] if key in dict and not dict[key]==None else ''
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

    # person related entities
    prp = ktm.PersonRelatestoPerson.select()
    prpDictList = entity_json_dict_list(prp)
    persons = ktm.Person.select()
    personsDictList = entity_json_dict_list(persons)

    # logging.debug('populated Subject, Work, Person  and related in-memory tables')

    graph_subject = refreshGraph(subjectsDictList, srsDictList)
    tree_Navigate(graph_subject, graph_subject['aum'], subjectsDictList, {'aum':'1001'}, 'aum')
    graph_work = refreshGraph(worksDictList, wrwDictList, entity='work')
    tree_Navigate(graph_work, graph_work['all'], worksDictList, {'all':'1001'}, 'all', entity='work')
    graph_person = refreshGraph(personsDictList, prpDictList, entity='person')
    tree_Navigate(graph_person, graph_person['all'], personsDictList, {'all':'1001'}, 'all', entity='person')


if __name__ == '__main__':
    main()
