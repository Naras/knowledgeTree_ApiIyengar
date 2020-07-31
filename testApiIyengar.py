
import json, ast, requests, unittest
from peewee import *
import knowledgeTreeModelSmall as ktm
import networkx as nx
from networkx.readwrite import json_graph
import random, string

def find_relation(subject1,subject2):
    for dict in srsJson:
        # dict = item #ast.literal_eval(item)
        if (dict['subject1'] == subject1) and (dict['subject2'] == subject2):
          return dict['relation']
    return None
def find_relations(subject):  # find all relations a subject has with another subject
    relations = []
    for item in srsJson:
        dict = item #ast.literal_eval(item)
        if dict['subject2'] == subject:
            # print dict
            dictitem = {'related': dict['subject1'], 'relation': dict['relation']}
            if 'sortorder' in dict: dictitem['sortorder']=dict['sortorder']
            relations.append(dictitem)
    return relations
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
                # print ('name:'+fld_name + ' value:'+str(fld_value))
                withoutCRLF = str(fld_value).replace('\r\n','')
                withoutCRLF = withoutCRLF.replace('\n','')
                withoutCRLF = withoutCRLF.replace("'", r'\"')
                # if fld_name == 'description':
                #     print(withoutCRLF)
                jsonElement += "'" + fld_name + "':'" + withoutCRLF + "',"  # escape /r/n
        elem = jsonElement[:-1] + '}'
        # elem = ast.literal_eval(jsonElement2)
        # print elem
        rowsJson.append(ast.literal_eval(elem))
    return rowsJson
def create_relation(subject1,subject2,relation,sortorder=None):
    # for item in srsJson:
    #     dict = ast.literal_eval(item)
    #     if (dict['subject1'] == subject1) and (dict['subject2'] == subject2) and (dict['relations'] == relation): #duplicate relation
    #       return False
    if (find_item_json_dict_list(subjectsJson,'id',subject1) is None) or (find_item_json_dict_list(subjectsJson,'id',subject2) is None) or (find_item_json_dict_list(ssrJson,'id',relation) is None):
        return False  # either of the subjects or relation not valid
    elif find_relation(subject1,subject2) is not None:  # subjects are already related
        return False
    else:
        try:
            dict = {'subject1':subject1,'subject2':subject2,'relation':relation,'sortorder':sortorder}
            srsJson.append(dict)
            ktm.SubjectRelatestoSubject.create(subject1=subject1,subject2=subject2,relation=relation,sortorder=sortorder)
        except IntegrityError:
            print('Failed to create relation:', dict)
            return False
    return True
def update_relation(subject2,relation=None,sortorder=None):
    subject1 = find_relations(subject2)[0]['related']   # a list of subject1s - usually only one expected
    if (find_item_json_dict_list(subjectsJson,'id',subject1) is None) or (find_item_json_dict_list(subjectsJson,'id',subject2) is None) \
            or (find_item_json_dict_list(ssrJson,'id',relation) is None):
        return False  # either of the subjects or relation not valid
    else:
        try:
            # update the subject relations and sort order on the db
            replace_relation(subject1,subject2,relation,sortorder)
            srsNew = ktm.SubjectRelatestoSubject.get(ktm.SubjectRelatestoSubject.subject1==subject1,ktm.SubjectRelatestoSubject.subject2==subject2)
            if relation is not None:srsNew.relation = relation
            if sortorder is not None:srsNew.sortorder = sortorder
            srsNew.save()
        except IntegrityError:
            print('Failed to update relation:', dict)
            return False
    return True
def replace_relation(subject1,subject2,relation=None,sortorder=None):
    for dict in srsJson:
        if (dict['subject1'] == subject1) and (dict['subject2'] == subject2):
          if relation is not None: dict['relation'] = relation
          if sortorder is not None: dict['sortorder'] = sortorder
          return dict
    return None
def delete_relation(subject1,subject2,relation):
    found = False
    for indx in range(len(srsJson)):  # find and remove the entry in Json array
        dict = srsJson[indx] #ast.literal_eval(srsJson[indx])
        # print dict
        if (dict['subject1'] == subject1) and (dict['subject2'] == subject2) and (dict['relation'] == relation):
            del srsJson[indx]
            found = True
            break;
    if not found: return False
    # if (find_item_json_dict_list(subjectsJson,'id',subject1) is None) or (find_item_json_dict_list(subjectsJson,'id',subject2) is None) or (find_item_json_dict_list(ssrJson,'id',relation) is None):
    #     return False # either of the subjects or relation not valid
    else:
        try:
            srs = ktm.SubjectRelatestoSubject.get(subject1=subject1,subject2=subject2,relation=relation)
            srs.delete_instance()
            return True
        except:
            print('Failed to delete relation:')  #, dict
            return False
def refreshGraph():
    g = nx.Graph()
    for row in subjectsJson:
        g.add_node(row['id'])
        g.node[row['id']]['name'] = row['name']
        if 'description' in row: g.node[row['id']]['description'] = row['description']
    for row in srsJson:
        g.add_edge(row['subject1'],row['subject2'])
        g[row['subject1']][row['subject2']]['relation'] = row['relation']
        if 'sortorder' in row:
            g[row['subject1']][row['subject2']]['sortorder'] = row['sortorder']
            # print row['sortorder']
        else:g[row['subject1']][row['subject2']]['sortorder'] = '99'
        # print g[row['subject1']][row['subject2']]
    return g
def add_name_description(td):
    dict = find_item_json_dict_list(subjectsJson,'id',td['id'])
    if not (dict == None):
        if 'name' in dict: td['name'] = dict['name']
        if 'description' in dict: td['description'] = dict['description']
        parent = find_item_json_dict_list(srsJson,'subject2',td['id']);
        if not (parent == None): td['parent'] = parent['subject1'];
        rel = find_relations(dict['id'])
        if not (rel==[]):
            td['relation']=rel[0]['relation']
            if 'sortorder' in rel[0]: td['sortorder']=rel[0]['sortorder']
        if 'children' in td:
            for child in td['children']:
                child = add_name_description(child)
    return td
def move_relation(subject,newparent,newrelation=None,sortorder=None):  # moves a subject from one parent to another - the subtree moves
    relations=find_relations(subject)
    delete_relation(relations[0]['related'],subject,relations[0]['relation'])
    if newrelation == None: newrelation = relations[0]['relation']
    return create_relation(newparent,subject,newrelation,sortorder)
def create_subject(subject):
    if find_item_json_dict_list(subjectsJson,'id',subject['id']) is not None:
        # generate a random string and concatenate
        subject['id'] = (subject['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    subjectsJson.append(subject)
    ktm.Subject.create(id=subject['id'],name=subject['name'],description=subject['description'])
    return {'subject': subject}
def create_subject_with_relation(subject_related_relation):
    dict = subject_related_relation #json.loads(subject_related_relation)
    subject2 = dict['subject']
    subject1id = dict['related']
    relation = dict['relation']
    if 'sortorder' in dict: sortorder = dict['sortorder']
    else: sortorder = None
    if find_item_json_dict_list(subjectsJson,'id',subject1id) is None:
        return None
    if find_item_json_dict_list(subjectsJson,'id',subject2['id']) is not None:
        # generate a random string and concatenate
        subject2['id'] = (subject2['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    create_subject(subject2)
    return create_relation(subject1id,subject2['id'],relation,sortorder)
def delete_subject(sub_id):
    sub = find_item_json_dict_list(subjectsJson,'id',sub_id)
    if sub is None or len(sub) == 0:
        return False
    for subj_index in range(len(subjectsJson)):
        # print subj_index,subjectsJson[subj_index],type(subjectsJson[subj_index])
        # subj_as_dict = ast.literal_eval(subjectsJson[subj_index])
        subj_as_dict = subjectsJson[subj_index]
        if (subj_as_dict['id'] == sub['id'] or subj_as_dict[u'id'] == sub['id'] or subj_as_dict['id'] == sub[u'id']):
            # print 'db delete:', subj_as_dict, type(subj_as_dict)
            subj = ktm.Subject.get(ktm.Subject.id == subj_as_dict['id'])
            subj.delete_instance()
            del subjectsJson[subj_index]
            break
    # subjectsJson.remove(sub)
    return True #subj_as_dict
def delete_subject_with_relation(sub_id):
    relations = find_relations(sub_id)
    for subject_with_relation in relations:
        subject1 = subject_with_relation['related']
        relation = subject_with_relation['relation']
        delete_relation(subject1,sub_id,relation) # each relation with another subject1 removed
    delete_subject(sub_id)
    return True
def update_subject(sub_id,sub_in):
    for index in range(len(subjectsJson)):
        # json_acceptable_string = subjectsJson[index].replace("'", "\"")
        dict = subjectsJson[index]
        if dict['id'] == sub_id:
            if 'name' in sub_in: dict['name'] = sub_in['name']
            if 'description' in sub_in: dict['description'] = sub_in['description']
            subjectsJson[index] = dict #json.dumps(dict)
            subj = ktm.Subject.get(ktm.Subject.id == sub_id)
            subj.name = dict['name']
            subj.description = dict['description']
            subj.save()
            # update relation and sortorder if given
            if 'relation' in sub_in:
                if 'sortorder' in sub_in: update_relation(sub_id,sub_in['relation'],sub_in['sortorder'])
                else: update_relation(sub_id,sub_in['relation'])
            else:
                if 'sortorder' in sub_in: update_relation(sub_id,sub_in['sortorder'])
            return subjectsJson[index]
    return None
def copy_subject(id,target):  # copy a source to a target parent
    row_subject = find_item_json_dict_list(subjectsJson,'id',id)
    if row_subject is None: return None
    row_srs = find_item_json_dict_list(srsJson,'subject2',id)
    if row_srs is None: return None
    new_id = (id  + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    return create_subject_with_relation({'subject':{'id':new_id,'name':row_subject['name'], \
                                 'description':row_subject['description']}, \
                                  'relation':row_srs['relation'],'related':target,'sortorder':row_srs['sortorder']})
def copy_children(id,target):
    children = []
    for item in srsJson:
        if item['subject1'] == id:
            children.append(item)
    for child in children:
        copy_subject(child['subject2'], target)
        copy_children(child['subject2'],target)
    return children
def delete_children(id):
    children = []
    for item in srsJson:
        if item['subject1'] == id:
            children.append(item)
    for child in children: delete_children(child['subject2'])
    # check if subject has work connections and remove them
    relations = find_subject_allwork_relations(id)
    for dict in relations: subject_work_delete_relation(dict['subject'],dict['work'],dict['relation'])
    return delete_subject_with_relation(id)
def work_find_relation(work1,work2):
    for dict in wrwJson:
        # dict = item #ast.literal_eval(item)
        if (dict['work1'] == work1) and (dict['work2'] == work2):
          return dict['relation']
    return None
def work_find_relations(work):  # find all relations a subject has with another subject
    relations = []
    for item in wrwJson:
        dict = item #ast.literal_eval(item)
        if dict['work2'] == work:
            # print dict
            dictitem = {'related': dict['work1'], 'relation': dict['relation']}
            if 'sortorder' in dict: dictitem['sortorder']=dict['sortorder']
            relations.append(dictitem)
    return relations

def work_create_relation(work1,work2,relation,sortorder=None):
    # for item in wrwJson:
    #     dict = ast.literal_eval(item)
    #     if (dict['work1'] == work1) and (dict['work2'] == work2) and (dict['relations'] == relation): #duplicate relation
    #       return False
    if (find_item_json_dict_list(worksJson,'id',work1) is None) or (find_item_json_dict_list(worksJson,'id',work2) is None) or (find_item_json_dict_list(wwrJson,'id',relation) is None):
        return False  # either of the works or relation not valid
    elif work_find_relation(work1,work2) is not None:  # works are already related
        return False
    else:
        try:
            dict = {'work1':work1,'work2':work2,'relation':relation,'sortorder':sortorder}
            wrwJson.append(dict)
            ktm.WorkRelatestoWork.create(work1=work1,work2=work2,relation=relation,sortorder=sortorder)
        except IntegrityError:
            print('Failed to create work relation:', dict)
            return False
    return True
def work_update_relation(work2,relation=None,sortorder=None):
    work1 = work_find_relations(work2)[0]['related']   # a list of work1s - usually only one expected
    if (find_item_json_dict_list(worksJson,'id',work1) is None) or (find_item_json_dict_list(worksJson,'id',work2) is None) \
            or (find_item_json_dict_list(wwrJson,'id',relation) is None):
        return False  # either of the works or relation not valid
    else:
        try:
            # update the subject relations and sort order on the db
            work_replace_relation(work1,work2,relation,sortorder)
            wrwNew = ktm.WorkRelatestoWork.get(ktm.WorkRelatestoWork.work1==work1,ktm.WorkRelatestoWork.work2==work2)
            if relation is not None:wrwNew.relation = relation
            if sortorder is not None:wrwNew.sortorder = sortorder
            wrwNew.save()
        except IntegrityError:
            print('Failed to update work relation:', dict)
            return False
    return True
def work_replace_relation(work1,work2,relation=None,sortorder=None):
    for dict in wrwJson:
        if (dict['work1'] == work1) and (dict['work2'] == work2):
          if relation is not None: dict['relation'] = relation
          if sortorder is not None: dict['sortorder'] = sortorder
          return dict
    return None
def work_delete_relation(work1,work2,relation):
    found = False
    for indx in range(len(wrwJson)):  # find and remove the entry in Json array
        dict = wrwJson[indx] #ast.literal_eval(wrwJson[indx])
        # print dict
        if (dict['work1'] == work1) and (dict['work2'] == work2) and (dict['relation'] == relation):
            del wrwJson[indx]
            found = True
            break;
    if not found: return False
    # if (find_item_json_dict_list(worksJson,'id',work1) is None) or (find_item_json_dict_list(worksJson,'id',work2) is None) or (find_item_json_dict_list(wwrJson,'id',relation) is None):
    #     return False # either of the works or relation not valid
    else:
        try:
            wrw = ktm.WorkRelatestoWork.get(work1=work1,work2=work2,relation=relation)
            wrw.delete_instance()
            return True
        except:
            print('Failed to delete work relation:')  #, dict
            return False
def work_refreshGraph():
    g = nx.Graph()
    for row in worksJson:
        g.add_node(row['id'])
        g.node[row['id']]['name'] = row['name']
        if 'description' in row: g.node[row['id']]['description'] = row['description']
    for row in wrwJson:
        g.add_edge(row['work1'],row['work2'])
        g[row['work1']][row['work2']]['relation'] = row['relation']
        if 'sortorder' in row:
            g[row['work1']][row['work2']]['sortorder'] = row['sortorder']
            # print row['sortorder']
        else:g[row['work1']][row['work2']]['sortorder'] = '99'
        # print g[row['work1']][row['work2']]
    return g
def work_add_name_description(td):
    dict = find_item_json_dict_list(worksJson,'id',td['id'])
    if not (dict == None):
        if 'name' in dict: td['name'] = dict['name']
        if 'description' in dict: td['description'] = dict['description']
        rel = work_find_relations(dict['id'])
        if not (rel==[]):
            td['relation']=rel[0]['relation']
            if 'sortorder' in rel[0]: td['sortorder']=rel[0]['sortorder']
        if 'children' in td:
            for child in td['children']:
                child = work_add_name_description(child)
    return td
def work_move_relation(work,newparent,newrelation=None,sortorder=None):  # moves a work from one parent to another - the subtree moves
    relations=work_find_relations(work)
    work_delete_relation(relations[0]['related'],work,relations[0]['relation'])
    if newrelation == None: newrelation = relations[0]['relation']
    return work_create_relation(newparent,work,newrelation,sortorder)
def work_create(work):
    if find_item_json_dict_list(worksJson,'id',work['id']) is not None:
        # generate a random string and concatenate
        work['id'] = (work['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    worksJson.append(work)
    ktm.Work.create(id=work['id'],name=work['name'],description=work['description'])
    return {'work': work}
def work_create_with_relation(work_related_relation):
    dict = work_related_relation #json.loads(work_related_relation)
    work2 = dict['work']
    work1id = dict['related']
    relation = dict['relation']
    if 'sortorder' in dict: sortorder = dict['sortorder']
    else: sortorder = None
    if find_item_json_dict_list(worksJson,'id',work1id) is None:
        return None
    if find_item_json_dict_list(worksJson,'id',work2['id']) is not None:
        # generate a random string and concatenate
        work2['id'] = (work2['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    work_create(work2)
    return work_create_relation(work1id,work2['id'],relation,sortorder)
def work_delete(wrk_id):
    wrk = find_item_json_dict_list(worksJson,'id',wrk_id)
    if wrk is None or len(wrk) == 0:
        return False
    for work_index in range(len(worksJson)):
        # print subj_index,worksJson[subj_index],type(worksJson[subj_index])
        # subj_as_dict = ast.literal_eval(worksJson[subj_index])
        work_as_dict = worksJson[work_index]
        if (work_as_dict['id'] == wrk['id'] or work_as_dict[u'id'] == wrk['id'] or work_as_dict['id'] == wrk[u'id']):
            # print 'db delete:', subj_as_dict, type(subj_as_dict)
            workx = ktm.Work.get(ktm.Work.id == work_as_dict['id'])
            workx.delete_instance()
            del worksJson[work_index]
            break
    # worksJson.remove(sub)
    return True #subj_as_dict
def work_delete_with_relation(wrk_id):
    relations = work_find_relations(wrk_id)
    for work_with_relation in relations:
        work1 = work_with_relation['related']
        relation = work_with_relation['relation']
        work_delete_relation(work1,wrk_id,relation) # each relation with another work1 removed
    work_delete(wrk_id)
    return True
def work_update(wrk_id,wrk_in):
    for index in range(len(worksJson)):
        # json_acceptable_string = worksJson[index].replace("'", "\"")
        dict = worksJson[index]
        if dict['id'] == wrk_id:
            if 'name' in wrk_in: dict['name'] = wrk_in['name']
            if 'description' in wrk_in: dict['description'] = wrk_in['description']
            worksJson[index] = dict #json.dumps(dict)
            subj = ktm.Work.get(ktm.Work.id == wrk_id)
            subj.name = dict['name']
            subj.description = dict['description']
            subj.save()
            # update relation and sortorder if given
            if 'relation' in wrk_in:
                if 'sortorder' in wrk_in: work_update_relation(wrk_id,wrk_in['relation'],wrk_in['sortorder'])
                else: work_update_relation(wrk_id,wrk_in['relation'])
            else:
                if 'sortorder' in wrk_in: work_update_relation(wrk_id,wrk_in['sortorder'])
            return worksJson[index]
    return None

def find_subject_work_relations(subject,work):
    relations = []
    for dict in shwJson:
        if dict['subject'] == subject and dict['work'] == work:
            relations.append(dict)
    return relations
def find_subject_allwork_relations(subject):
    relations = []
    for dict in shwJson:
        if dict['subject'] == subject:
            relations.append(dict)
    return relations
def find_work_allsubject_relations(work):
    relations = []
    for dict in shwJson:
        if dict['work'] == work:
            relations.append(dict)
    return relations
def subject_work_create_relation(subject,work,relation):
    if find_subject_work_relations(subject,work) != []:  # subject/work are already related
        return False
    else:
        try:
            dict = {'subject':subject,'work':work,'relation':relation}
            shwJson.append(dict)
            # print 'creating subject_work relation:'+ dict['subject'] + '-'+ dict['work'] + '-'+relation
            ktm.SubjectHasWork.create(subject=subject,work=work,relation=relation)
        except IntegrityError:
                print('Failed to create subject-work relation:', dict)
                return False
def subject_work_delete_relation(subject,work,relation):
    found = False
    for indx in range(len(shwJson)):  # find and remove the entry in Json array
        dict = shwJson[indx] #ast.literal_eval(srsJson[indx])
        # print dict
        if (dict['subject'] == subject) and (dict['work'] == work) and (dict['relation'] == relation):
            del shwJson[indx]
            found = True
            break;
    if not found: return False
    # if (find_item_json_dict_list(subjectsJson,'id',subject1) is None) or (find_item_json_dict_list(subjectsJson,'id',subject2) is None) or (find_item_json_dict_list(ssrJson,'id',relation) is None):
    #     return False # either of the subjects or relation not valid
    else:
        try:
            # shw = ktm.SubjectHasWork.get(subject=subject,work=work,relation=relation)
            # shw.delete_instance()
            qry = ktm.SubjectHasWork.delete().where(ktm.SubjectHasWork.subject==subject,ktm.SubjectHasWork.work==work,ktm.SubjectHasWork.relation==relation)
            qry.execute()
            return True
        except:
            print ('Failed to delete subject-work relation:'+ subject + '-' + work + '-' + relation)  #, dict
            return False
def subject_work_refreshGraph(subject):
    g = nx.Graph()
    for row in shwJson:
        if row['subject']==subject:
            g.add_node(row['subject'])
            if row['subject'] == row['work']: wrk=row['work']+'_pramaaNa'
            else: wrk=row['work']
            g.add_node(wrk)
            g.add_edge(row['subject'],wrk)
            g[row['subject']][wrk]['relation'] = row['relation']
    if g.number_of_edges()==0:g.add_node(subject) # no work relatons for this subject
    return g
def work_subject_refreshGraph(work):
    g = nx.Graph()
    for row in shwJson:
        if row['work']==work:
            if row['subject'] == row['work']: sub=row['subject']+'_pramEya'
            else: sub=row['subject']
            g.add_node(sub)
            g.add_node(row['work'])
            g.add_edge(row['work'],sub)
            g[row['work']][sub]['relation'] = row['relation']
            break;
    if g.number_of_edges()==0:g.add_node(work) # no subject relatons for this work
    return g
def subject_work_add_relation(td):
    # print td
    for elem in td['children']:
        dict = find_item_json_dict_list(shwJson,'work',elem['id'])
        if not (dict == None):
            if 'relation' in dict: elem['relation'] = dict['relation']
    return td
def work_subject_add_relation(td):
    # print td
    for elem in td['children']:
        dict = find_item_json_dict_list(shwJson,'subject',elem['id'])
        if not (dict == None):
            if 'relation' in dict: elem['relation'] = dict['relation']
    return td

def person_find_relation(person1,person2):
    for dict in prpJson:
        # dict = item #ast.literal_eval(item)
        if (dict['person1'] == person1) and (dict['person2'] == person2):
          return dict['relation']
    return None
def person_find_relations(person):  # find all relations a subject has with another subject
    relations = []
    for item in prpJson:
        dict = item #ast.literal_eval(item)
        if dict['person2'] == person:
            # print dict
            dictitem = {'related': dict['person1'], 'relation': dict['relation']}
            relations.append(dictitem)
    return relations
def copy_work(id,target):  # copy a source to a target parent
    row_work = find_item_json_dict_list(worksJson,'id',id)
    if row_work is None: return None
    row_wrw = find_item_json_dict_list(wrwJson,'work2',id)
    if row_wrw is None: return None
    new_id = (id  + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    return work_create_with_relation({'work':{'id':new_id,'name':row_work['name'], \
                                 'description':row_work['description']}, \
                                  'relation':row_wrw['relation'],'related':target,'sortorder':row_wrw['sortorder']})
def work_copy_children(id,target):
    children = []
    for item in wrwJson:
        if item['work1'] == id:
            children.append(item)
    for child in children:
        copy_work(child['work2'], target)
        work_copy_children(child['work2'],target)
    return children
def work_delete_children(id):
    children = []
    for item in wrwJson:
        if item['work1'] == id:
            children.append(item)
    for child in children: work_delete_children(child['work2'])
    # check if work has subject connections and remove them
    relations = find_work_allsubject_relations(id)
    for dict in relations: subject_work_delete_relation(dict['subject'],dict['work'],dict['relation'])
    relations = find_work_allperson_relations(id)
    for dict in relations: person_work_delete_relation(dict['person'],dict['work'],dict['relation'])
    return work_delete_with_relation(id)

def person_create_relation(person1,person2,relation):
    if (find_item_json_dict_list(personsJson,'id',person1) is None) or (find_item_json_dict_list(personsJson,'id',person2) is None) or (find_item_json_dict_list(pprJson,'id',relation) is None):
        return False  # either of the persons or relation not valid
    elif person_find_relation(person1,person2) is not None:  # persons are already related
        return False
    else:
        try:
            dict = {'person1':person1,'person2':person2,'relation':relation}
            prpJson.append(dict)
            ktm.PersonRelatestoPerson.create(person1=person1,person2=person2,relation=relation)
        except IntegrityError:
            print('Failed to create person relation:', dict)
            return False
    return True
def person_update_relation(person2,relation=None):
    person1 = person_find_relations(person2)[0]['related']   # a list of person1s - usually only one expected
    if (find_item_json_dict_list(personsJson,'id',person1) is None) or (find_item_json_dict_list(personsJson,'id',person2) is None) \
            or (find_item_json_dict_list(wwrJson,'id',relation) is None):
        return False  # either of the persons or relation not valid
    else:
        try:
            # update the person relations on the db
            person_replace_relation(person1,person2,relation)
            prpNew = ktm.PersonRelatestoPerson.get(ktm.PersonRelatestoPerson.person1==person1,ktm.PersonRelatestoPerson.person2==person2)
            if relation is not None:prpNew.relation = relation
            prpNew.save()
        except IntegrityError:
            print('Failed to update person relation:', dict)
            return False
    return True
def person_replace_relation(person1,person2,relation=None):
    for dict in prpJson:
        if (dict['person1'] == person1) and (dict['person2'] == person2):
          if relation is not None: dict['relation'] = relation
          return dict
    return None
def person_delete_relation(person1,person2,relation):
    found = False
    for indx in range(len(wrwJson)):  # find and remove the entry in Json array
        dict = prpJson[indx] #ast.literal_eval(wrwJson[indx])
        # print dict
        if (dict['person1'] == person1) and (dict['person2'] == person2) and (dict['relation'] == relation):
            del prpJson[indx]
            found = True
            break;
    if not found: return False
    # if (find_item_json_dict_list(personsJson,'id',person1) is None) or (find_item_json_dict_list(personsJson,'id',person2) is None) or (find_item_json_dict_list(wwrJson,'id',relation) is None):
    #     return False # either of the persons or relation not valid
    else:
        try:
            prp = ktm.PersonRelatestoPerson.get(person1=person1,person2=person2,relation=relation)
            prp.delete_instance()
            return True
        except:
            print('Failed to delete person relation:')  #, dict
            return False
def person_refreshGraph():
    g = nx.Graph()
    for row in personsJson:
        g.add_node(row['id'])
        if 'first' in row: g.node[row['id']]['first'] = row['first']
        if 'last' in row: g.node[row['id']]['last'] = row['last']
        if 'middle' in row: g.node[row['id']]['middle'] = row['middle']
        if 'nick' in row: g.node[row['id']]['nick'] = row['nick']
        if 'other' in row: g.node[row['id']]['other'] = row['other']
    for row in prpJson:
        g.add_edge(row['person1'],row['person2'])
        g[row['person1']][row['person2']]['relation'] = row['relation']
        # print g[row['person1']][row['person2']]
    return g
def person_add_names(td):
    dict = find_item_json_dict_list(personsJson,'id',td['id'])
    if not (dict == None):
        if 'first' in dict: td['first'] = dict['first']
        if 'last' in dict: td['last'] = dict['last']
        if 'middle' in dict: td['middle'] = dict['middle']
        if 'nick' in dict: td['nick'] = dict['nick']
        if 'other' in dict: td['other'] = dict['other']
        rel = person_find_relations(dict['id'])
        if not (rel==[]):
            td['relation']=rel[0]['relation']
        if 'children' in td:
            for child in td['children']:
                child = person_add_names(child)
    return td
def person_move_relation(person,newparent,newrelation=None):  # moves a person from one parent to another - the subtree moves
    relations=person_find_relations(person)
    person_delete_relation(relations[0]['related'],person,relations[0]['relation'])
    if newrelation == None: newrelation = relations[0]['relation']
    return person_create_relation(newparent,person,newrelation)
def person_create(person):
    if find_item_json_dict_list(personsJson,'id',person['id']) is not None:
        # generate a random string and concatenate
        person['id'] = (person['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    personsJson.append(person)

    if 'first' in person: first=person['first']
    else: first = None;
    if 'middle' in person: middle=person['middle']
    else: middle = None;
    if 'last' in person: last=person['last']
    else: last = None;
    if 'initials' in person: initials=person['initials']
    else: initials = None;
    if 'nick' in person: nick=person['nick']
    else: nick = None;
    if 'other' in person: other=person['other']
    else: other = None;
    if 'birth' in person: birth=person['birth']
    else: birth = None;
    if 'living' in person: living=person['living']
    else: living = None;
    if 'death' in person:
        death=person['death']
        living=None;
    else:
        death = None;
        living=1
    if 'biography' in person: biography=person['biography']
    else: biography = None;

    ktm.Person.create(id=person['id'],first=first,middle=middle,last=last,initials=initials,nick=nick,other=other, \
                      living=living,birth=birth,death=death,biography=biography)
    return {'person': person}
def person_create_with_relation(person_related_relation):
    dict = person_related_relation #json.loads(person_related_relation)
    person2 = dict['person']
    person1id = dict['related']
    relation = dict['relation']
    if find_item_json_dict_list(personsJson,'id',person1id) is None:
        return None
    if find_item_json_dict_list(personsJson,'id',person2['id']) is not None:
        # generate a random string and concatenate
        person2['id'] = (person2['id'] + ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16)))[0:19]
    person_create(person2)
    return person_create_relation(person1id,person2['id'],relation)
def person_delete(prs_id):
    prs = find_item_json_dict_list(personsJson,'id',prs_id)
    if prs is None or len(prs) == 0:
        return False
    for person_index in range(len(personsJson)):
        # print subj_index,personsJson[subj_index],type(personsJson[subj_index])
        # subj_as_dict = ast.literal_eval(personsJson[subj_index])
        person_as_dict = personsJson[person_index]
        if (person_as_dict['id'] == prs['id'] or person_as_dict[u'id'] == prs['id'] or person_as_dict['id'] == prs[u'id']):
            # print 'db delete:', subj_as_dict, type(subj_as_dict)
            personx = ktm.Person.get(ktm.Person.id == person_as_dict['id'])
            personx.delete_instance()
            del personsJson[person_index]
            break
    # personsJson.remove(sub)
    return True #subj_as_dict
def person_delete_with_relation(prs_id):
    relations = person_find_relations(prs_id)
    for person_with_relation in relations:
        person1 = person_with_relation['related']
        relation = person_with_relation['relation']
        person_delete_relation(person1,prs_id,relation) # each relation with another person1 removed
    person_delete(prs_id)
    return True
def person_update(prs_id,prs_in):
    for index in range(len(personsJson)):
        # json_acceptable_string = personsJson[index].replace("'", "\"")
        dict = personsJson[index]
        if dict['id'] == prs_id:
            if 'first' in prs_in: dict['first'] = prs_in['first']
            if 'last' in prs_in: dict['last'] = prs_in['last']
            if 'middle' in prs_in: dict['middle'] = prs_in['middle']
            if 'nick' in prs_in: dict['nick'] = prs_in['nick']
            if 'other' in prs_in: dict['other'] = prs_in['other']
            if 'living' in prs_in: dict['other'] = prs_in['living']
            if 'birth' in prs_in: dict['birth'] = prs_in['birth']
            if 'death' in prs_in:
                dict['death'] = prs_in['death']
                dict['living'] = None
            if 'biography' in prs_in: dict['biography'] = prs_in['biography']
            personsJson[index] = dict #json.dumps(dict)
            pers = ktm.Person.get(ktm.Person.id == prs_id)
            pers.first = dict['first']
            pers.last = dict['last']
            pers.middle = dict['middle']
            pers.nick = dict['nick']
            pers.other = dict['other']
            pers.living = dict['living']
            pers.birth = dict['birth']
            pers.death = dict['death']
            pers.biography = dict['biography']
            pers.save()
            # update relation if given
            if 'relation' in prs_in:
                person_update_relation(prs_id,prs_in['relation'])
            return personsJson[index]
    return None

def find_person_work_relations(person,work):
    relations = []
    for dict in phwJson:
        if dict['person'] == person and dict['work'] == work:
            # print dict
            relations.append(dict)
    return relations
def find_person_allwork_relations(person):
    relations = []
    for dict in phwJson:
        if dict['person'] == person:
            # print dict
            relations.append(dict)
    return relations
def find_work_allperson_relations(work):
    relations = []
    for dict in phwJson:
        if dict['work'] == work:
            # print dict
            relations.append(dict)
    return relations
def person_work_create_relation(person,work,relation):
    if find_person_work_relations(person,work) != []:  # person/work are already related
        return False
    else:
        try:
            dict = {'person':person,'work':work,'relation':relation}
            phwJson.append(dict)
            # print 'creating person_work relation:'+ dict['person'] + '-'+ dict['work'] + '-'+relation
            ktm.PersonHasWork.create(person=person,work=work,relation=relation)
        except IntegrityError:
                print('Failed to create person-work relation:', dict)
                return False
def person_work_delete_relation(person,work,relation):
    found = False
    for indx in range(len(phwJson)):  # find and remove the entry in Json array
        dict = phwJson[indx] #ast.literal_eval(srsJson[indx])
        # print dict
        if (dict['person'] == person) and (dict['work'] == work) and (dict['relation'] == relation):
            del phwJson[indx]
            found = True
            break;
    if not found: return False
    # if (find_item_json_dict_list(personsJson,'id',person1) is None) or (find_item_json_dict_list(personsJson,'id',person2) is None) or (find_item_json_dict_list(ssrJson,'id',relation) is None):
    #     return False # either of the persons or relation not valid
    else:
        try:
            # shw = ktm.PersonHasWork.get(person=person,work=work,relation=relation)
            # shw.delete_instance()
            qry = ktm.PersonHasWork.delete().where(ktm.PersonHasWork.person==person,ktm.PersonHasWork.work==work,ktm.PersonHasWork.relation==relation)
            qry.execute()
            return True
        except:
            print ('Failed to delete person-work relation:'+ person + '-' + work + '-' + relation)  #, dict
            return False
def person_work_refreshGraph(person):
    g = nx.Graph()
    for row in phwJson:
        if row['person']==person:
            g.add_node(row['person'])
            if row['person'] == row['work']: wrk=row['work']+'_pramaaNa'
            else: wrk=row['work']
            g.add_node(wrk)
            g.add_edge(row['person'],wrk)
            g[row['person']][wrk]['relation'] = row['relation']
    if g.number_of_edges()==0:g.add_node(person) # no work relatons for this person
    return g
def work_person_refreshGraph(work):
    g = nx.Graph()
    for row in phwJson:
        if row['work']==work:
            if row['person'] == row['work']: sub=row['person']+'_pramatha'
            else: sub=row['person']
            g.add_node(sub)
            g.add_node(row['work'])
            g.add_edge(row['work'],sub)
            g[row['work']][sub]['relation'] = row['relation']
            break;
    if g.number_of_edges()==0:g.add_node(work) # no person relatons for this work
    return g
def person_work_add_relation(td):
    # print td
    for elem in td['children']:
        dict = find_item_json_dict_list(shwJson,'work',elem['id'])
        if not (dict == None):
            if 'relation' in dict: elem['relation'] = dict['relation']
    return td
def work_person_add_relation(td):
    # print td
    for elem in td['children']:
        dict = find_item_json_dict_list(shwJson,'person',elem['id'])
        if not (dict == None):
            if 'relation' in dict: elem['relation'] = dict['relation']
    return td


ktm.database.connect()
# g.graph['person'] = ktm.Work.select()
# subjects = ktm.Work.select()

db = ktm.database
db.create_tables([ktm.Subject, ktm.SubjectSubjectRelation, ktm.SubjectRelatestoSubject, \
                  ktm.Work, ktm.WorkWorkRelation, ktm.WorkRelatestoWork, \
                  ktm.Person, ktm.PersonPersonRelation, ktm.PersonRelatestoPerson], \
                 safe=True)

# subject related entities
ssr = ktm.SubjectSubjectRelation.select()
ssrJson = entity_json_dict_list(ssr)
srs = ktm.SubjectRelatestoSubject.select()
srsJson = entity_json_dict_list(srs)
subjects = ktm.Subject.select()
subjectsJson = entity_json_dict_list(subjects)


# person related entities
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
class TestUM(unittest.TestCase):
    def test_subject_crud(self):  # subjects added, modified, related, moved, removed
        sub1 = {"id": "idtestParent", "name": "name-test-parent", "description": "description-test-parent"}
        sub2 = {"id": "idtestChild", "name": "name-test-child", "description": "description-test-child"}
        sub_with_relation = {'subject':sub2,'related':sub1['id'],'relation':'Anga','sortorder':65}

        # create a sample parent subject
        relations = ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'DARSHANA', 'DHARMA_DHARMI', 'JANYA_JANAKA',
                               'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA', 'ANGA', 'PRAKAARA_PRAKAARI', 'COMMON_PARENT', 'UDDHESHYA_VIDHEYA', 'UPAVEDA',
                               'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI']
        response = create_subject(sub1)
        self.assertEqual({'subject': {'description': 'description-test-parent', 'id': 'idtestParent', 'name': 'name-test-parent'}},response) # parent subject created

        # api iyengar cloud database
        # node_id = response
        # node_id["_id"] = "1001"
        # print(node_id)
        parentNode = addChild(self, "1001", random.choice(relations), 'name-test-parent', 'description-test-parent')
        print('parentNode: %s'%parentNode)

        # create a child subject with relation to parent
        self.assertEqual(True,create_subject_with_relation(sub_with_relation))
        parent = find_item_json_dict_list(subjectsJson,'id','idtestParent')
        child = find_item_json_dict_list(subjectsJson,'id','idtestChild')
        self.assertEqual({'description': 'description-test-parent', 'id': 'idtestParent', 'name': 'name-test-parent'},parent) # parent data correct
        self.assertEqual({'description': 'description-test-child', 'id': 'idtestChild', 'name': 'name-test-child'},child) # child data correct
        self.assertEqual([{'relation': 'Anga', 'sortorder': 65, 'related': 'idtestParent'}],find_relations(child['id']))
        self.assertEqual({'description': 'description-child-new', 'id': 'idtestChild', 'name': 'name-child-new'},
                         update_subject("idtestChild",{"name": "name-child-new", "description": "description-child-new","relation":"upa","sortorder":"87"})) # update relation/sortorder
        self.assertEqual([{'relation': 'upa', 'sortorder': '87', 'related': 'idtestParent'}],find_relations(child['id'])) # modified relation/sortorder correct

        # api iyengar cloud database
        childNode = addChild(self, parentNode["subject"]["_id"], random.choice(relations), 'name-test-child', 'description-test-child')
        print('childNode: %s'%childNode)

        # print '-'*55
        # for srs in wrwJson:print srs #,type(srs)

        # create a duplicate child subject with relation to parent
        sub2 = {"id": "idtestChild", "name": "name-test-child-duplicate", "description": "description-test-child-duplicate"}
        sub_with_relation = {'subject':sub2,'related':sub1['id'],'relation':'upa','sortorder':76}
        self.assertEqual(True,create_subject_with_relation(sub_with_relation))
        child_dup = find_item_json_dict_list(subjectsJson,'name','name-test-child-duplicate')
        self.assertEqual([{'relation': 'upa', 'sortorder': 76, 'related': 'idtestParent'}],find_relations(child_dup['id']))

        # create a new parent
        newparent = {"id": "idtestNewParent", "name": "name-test-newparent", "description": "description-test-newparent"} # create new parent
        response = create_subject(newparent)
        self.assertEqual({'subject': {'description': 'description-test-newparent', 'id': 'idtestNewParent', 'name': 'name-test-newparent'}},response)
        self.assertEqual(True,move_relation('idtestChild','idtestNewParent',newrelation='Anonya',sortorder=59)) # move child to new parent
        self.assertEqual([{'relation': 'Anonya', 'sortorder': 59, 'related': 'idtestNewParent'}],find_relations(child['id'])) # moved relation/sortorder correct

        self.assertEqual(True,delete_subject_with_relation(child['id'])) # remove child
        self.assertEqual(True,delete_subject_with_relation(child_dup['id'])) # remove duplicate child
        self.assertEqual(True,delete_subject(parent['id'])) # remove parent
        self.assertEqual(True,delete_subject(newparent['id'])) # remove new parent
        self.assertEqual(None,find_item_json_dict_list(subjectsJson,'id',parent['id'])) # parent does not exist
        self.assertEqual(None,find_item_json_dict_list(subjectsJson,'id',newparent['id']))  # new parent does not exist
        self.assertEqual(None,find_item_json_dict_list(subjectsJson,'id',child['id'])) # child does not exist
        self.assertEqual(None,find_item_json_dict_list(subjectsJson,'id',child_dup['id'])) # duplicate child does not exist
        self.assertEqual([],find_relations(child['id'])) # no relations for child

        #create a subtree with some children
        sub1 = {"id": "idtestParent", "name": "name-test-parent", "description": "description-test-parent"}
        response = create_subject(sub1)
        parent = find_item_json_dict_list(subjectsJson, 'id', 'idtestParent')
        self.assertEqual({'description': 'description-test-parent', 'id': 'idtestParent', 'name': 'name-test-parent'},
                         parent)  # parent data correct
        for id in ['idtestChild1','idtestChild2','idtestChild3']:
            sub2 = {"id": id, "name": "name-test-" + id, "description": "description-test-" + id}
            order = random.choice(range(1,10))
            sub_with_relation = {'subject':sub2,'related':sub1['id'],'relation':'Anga','sortorder':order}
            # create child subjects with relation to parent
            self.assertEqual(True,create_subject_with_relation(sub_with_relation))
            child = find_item_json_dict_list(subjectsJson,'id',id)
            self.assertEqual({'description': 'description-test-' + id, 'id': id, 'name': 'name-test-' + id},child) # child data correct
            self.assertEqual([{'relation': 'Anga', 'sortorder': order, 'related': 'idtestParent'}],find_relations(child['id']))
            self.assertEqual({'description': 'description-child-new', 'id': id, 'name': 'name-child-new'},
                             update_subject(id,{"name": "name-child-new", "description": "description-child-new",\
                                                "relation":"upa","sortorder":order + 10})) # update relation/sortorder
            self.assertEqual([{'relation': 'upa', 'sortorder': order + 10, 'related': 'idtestParent'}],find_relations(child['id'])) # modified relation/sortorder correct

        # create a new grand parent and copy a subtree to it.
        newparent = {"id": "idtestNewGrandParent", "name": "name-test-newparent", "description": "description-test-newparent"} # create new parent
        response = create_subject(newparent)
        self.assertEqual({'subject': {'description': 'description-test-newparent', 'id': 'idtestNewGrandParent', 'name': 'name-test-newparent'}},response)
        response = copy_children('idtestParent','idtestNewGrandParent')  # copy subtree
        # print ('copy subtree response: %s' % str(response))
        self.assertIn("'subject1': 'idtestParent'",str(response))
        self.assertIn("'subject2': 'idtestChild1'",str(response))
        self.assertIn("'subject2': 'idtestChild2'",str(response))
        self.assertIn("'subject2': 'idtestChild3'",str(response))
        self.assertIn("'relation': 'upa'",str(response))

        # print 'Subject Edges'
        # for srs in srsJson:print srs

        # g = refreshGraph()
        # write json formatted data

        json.dump(json_graph.node_link_data(refreshGraph()), open('jsondata/knowledgeTree-force.json','w'))
        print('Wrote node_id-link JSON data to jsondata/knowledgeTree-force.json')
        json.dump(add_name_description(json_graph.tree_data(nx.bfs_tree(refreshGraph(),"idtestNewGrandParent"),"idtestNewGrandParent")), open('jsondata/knowledgeTree-tree.json','w'))
        print('Wrote sub-tree JSON data to jsondata/knowledgeTree-tree.json')
        self.assertEqual(True, delete_children('idtestParent'))
        self.assertEqual(True, delete_children('idtestNewGrandParent'))
    def testNavigateToLevel(self):
            prefix = 'http://api.iyengarlabs.org/v1/'
            response = requests.get(prefix + 'rootsubject')
            self.assertEqual(200, response.status_code)
            responseAsDict = json.loads(response.text)
            # print(responseAsDict)
            self.assertIn('subject', responseAsDict)
            self.assertIn('title', responseAsDict['subject'])
            self.assertEqual('OM', responseAsDict['subject']['title'])
            self.assertIn('description', responseAsDict['subject'])
            self.assertEqual('Origin of everything', responseAsDict['subject']['description'])
            # self.assertIn('subject_relations', responseAsDict['subject'])
            if 'subject_relations' in responseAsDict['subject']:
                subject_relations = responseAsDict['subject']['subject_relations']
                getChildren(self, subject_relations)
            else: addChild(self, responseAsDict['subject'])
def getChildren(self, subject_relations):
        prefix = 'http://api.iyengarlabs.org/v1/'
        for entry in subject_relations:
            # print(entry)
            self.assertIn(entry['subjecttype'],
                          ['ADHAARA_ADHAARI', 'ANGA_ANGI', 'ANONYA_ASHRAYA', 'ASHRAYA_ASHREYI', 'AVAYAVI', 'DARSHANA',
                           'DHARMA_DHARMI', 'JANYA_JANAKA', 'KAARYA_KAARANA', 'NIRUPYA_NIRUPAKA', 'ANGA', 'PRAKAARA_PRAKAARI', 'COMMON_PARENT',
                           'UDDHESHYA_VIDHEYA', 'UPAVEDA', 'UPABRAHMYA_UPABRAHMANA', 'UPANISHAD', 'VISHAYA_VISHAYI'])
            Request_Url_child = entry['_links']['self']['href']
            if str(Request_Url_child).startswith('/v1'): Request_Url_child = prefix + Request_Url_child
            response = requests.get(Request_Url_child)
            # self.assertEqual(200, response.status_code)
            if response.status_code == 200:
                responseAsDict = json.loads(response.text)
                # for k,v in responseAsDict['subject'].items(): print('k:%s v:%s'%(k,v))
                node_id = responseAsDict['subject']['_id']
                if 'subject_relations' in responseAsDict['subject']:
                    # has child nodes/subtree
                    print('non-leaf node_id id:%s title:%s parent:%s\ndescription:%s\nchild exists - relation:%s id:%s' %
                      (responseAsDict['subject']['_id'], responseAsDict['subject']['title'],
                       responseAsDict['subject']['subject_parents'][0]['id'], responseAsDict['subject']['description'],
                       responseAsDict['subject']['subject_relations'][0]['subjecttype'],
                       responseAsDict['subject']['subject_relations'][0]['id']))
                    # print(responseAsDict['subject']['subject_relations'][0])
                    getChildren(self, responseAsDict['subject']['subject_relations'])
                    # print('node_id:%s subject:%s' % (node_id, responseAsDict['subject']['subject_relations'][0]))
                else:
                    # leaf node_id
                    print('leaf node_id id:%s title:%s parent:%s\ndescription:%s' %
                      (responseAsDict['subject']['_id'], responseAsDict['subject']['title'],
                       responseAsDict['subject']['subject_parents'][0]['id'], responseAsDict['subject']['description']))
                    # print('leaf node_id:%s parent:%s' % (node_id, responseAsDict['subject']['subject_parents'][0]['id']))
                    addChild(self, responseAsDict['subject'])

                self.assertIn('title', responseAsDict['subject'])
                self.assertIn('subject_parents', responseAsDict['subject'])
def addChild(self, node_id, rel, title, description):
        prefix = 'http://api.iyengarlabs.org/v1/'
        response = requests.post(prefix + 'subject/add',
                                 json={'title': title, 'description': description},
                                 headers={'parentid': node_id, "relation": rel})
        self.assertIn(response.status_code, [200, 201])
        responseAsDict = json.loads(response.text)
        created_id_child = responseAsDict['subject']['_id']
        # print('child:',responseAsDict)
        self.assertIn('title', responseAsDict['subject'])
        self.assertEqual(title, responseAsDict['subject']['title'])
        self.assertIn('description', responseAsDict['subject'])
        self.assertEqual(description, responseAsDict['subject']['description'])
        self.assertIn('id', responseAsDict['subject']['subject_parents'][0])
        self.assertEqual(node_id, responseAsDict['subject']['subject_parents'][0]['id'])
        response = requests.get(prefix + 'subject/' + node_id)
        self.assertIn(response.status_code, [200, 201])
        newnode = responseAsDict
        responseAsDict = json.loads(response.text)
        # print('node after:', responseAsDict)
        # self.assertIn('subjecttype', responseAsDict['subject']['subject_relations'][0])
        # self.assertIn(relations, responseAsDict['subject']['subject_relations'][0]['subjecttype'])
        # self.assertIn('id', responseAsDict['subject']['subject_relations'][0])
        # self.assertEqual(created_id_child, responseAsDict['subject']['subject_relations'][0]['id'])
        # response = requests.delete(prefix + 'subject/remove/' + node_id['_id'] + '?deletesubtree=true')
        # self.assertIn(response.status_code, [200, 201])
        # self.assertEqual('"OK"', response.text)
        return newnode
if __name__ == '__main__':
    unittest.main()