import psycopg2
import sys
import psycopg2.extras
from elasticsearch import Elasticsearch
 
def create_item_index():
	#Define our connection string

    conn_string = "host='localhost' dbname='test1' user='postgres' password='441989'"
 
	# print the connection string we will use to connect
    print "Connecting to database\n	->%s" % (conn_string)
 
	# get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    cursor.execute("select  items.id, items.properties, items.info_pack_id, items.item_type_id, items.parent_id, itags.tag_id, tags.name from items as items full outer join item_tags as itags on items.id=itags.item_id full outer join tags  on tags.id=itags.tag_id order by items.id")
    records = cursor.fetchall()
	# Then we connect to an elasticsearch server
    es = Elasticsearch()
    es.indices.create(index='learnapt', ignore=400)
    old_item_id=-1
    for record in records:
        parent_id=record[4]
        item_id=record[0]
        info_pack_id=record[2]
        item_type_id=record[3]
        tag=record[6]
        if record[1] is None:
            continue
        item_contents=record[1].split('", "')
        if item_id is old_item_id and tag is not None:
            document['item_tag'] = document['item_tag'] + '_' +tag
        else:
            document={'item_id':item_id,'info_pack_id':info_pack_id,'item_type_id':item_type_id}
            if tag is not None:
                document['item_tag']=tag
        for item_content in item_contents:
            key_value=item_content.strip().split('=>')
            if len(key_value)<2 or len(key_value)%2 is not 0:
                continue
            document['item_'+key_value[0].strip().replace('"','')]=key_value[1].strip().replace('"','')
        if item_id != old_item_id and old_item_id != -1:
            print 'item_id being inserted '+str(old_item_id)
            es.create('learnapt', 'item',old_document,int(old_item_id))
        old_item_id=item_id
        old_document=document
    print "Converted!\n "

def create_lesson_index():
	#Define our connection string

    conn_string = "host='localhost' dbname='test1' user='postgres' password='441989'"
 
	# print the connection string we will use to connect
    print "Connecting to database\n	->%s" % (conn_string)
 
	# get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    cursor.execute("select  lessons.id, lessons.name, lessons.slug, lessons.cover_image, lessons.sub_title, itags.tag_id, tags.name from info_packs as lessons full outer join info_pack_tags as itags on lessons.id=itags.info_pack_id full outer join tags  on tags.id=itags.tag_id order by lessons.id;")
    records = cursor.fetchall()
	# Then we connect to an elasticsearch server
    es = Elasticsearch()
    es.indices.create(index='learnapt', ignore=400)
    old_lesson_id=-1
    for record in records:
        lesson_id=record[0]
        lesson_name=record[1]
        lesson_slug=record[2]
        lesson_sub_title=record[4]
        lesson_cover_image=record[3]
        tag=record[6]
        if record[1] is None:
            continue
        if lesson_id is old_lesson_id and tag is not None:
            if 'lesson_tag' not in document:
                document['lesson_tag']=''    
            document['lesson_tag'] = document['lesson_tag'] + '_' +tag
        else:
            document={'lesson_id':lesson_id,'lesson_name':lesson_name, 'lesson_slug':lesson_slug, 'lesson_sub_title':lesson_sub_title, 'lesson_cover_image':lesson_cover_image}
            if tag is not None:
                document['lesson_tag']=tag
        if lesson_id != old_lesson_id and old_lesson_id != -1:
            print 'lesson_id being inserted '+str(old_lesson_id)
            es.create('learnapt', 'lesson',old_document,int(old_lesson_id))
        old_lesson_id=lesson_id
        old_document=document
    print "Converted!\n "

def create_user_index():
	#Define our connection string

    conn_string = "host='localhost' dbname='test1' user='postgres' password='441989'"
 
	# print the connection string we will use to connect
    print "Connecting to database\n	->%s" % (conn_string)
 
	# get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
 
	# conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    cursor.execute("select  lessons.id, lessons.name, lessons.slug, lessons.cover_image, lessons.sub_title, itags.tag_id, tags.name from info_packs as lessons full outer join info_pack_tags as itags on lessons.id=itags.info_pack_id full outer join tags  on tags.id=itags.tag_id order by lessons.id;")
    records = cursor.fetchall()
	# Then we connect to an elasticsearch server
    es = Elasticsearch()
    es.indices.create(index='learnapt', ignore=400)
    old_lesson_id=-1
    for record in records:
        lesson_id=record[0]
        lesson_name=record[1]
        lesson_slug=record[2]
        lesson_sub_title=record[4]
        lesson_cover_image=record[3]
        tag=record[6]
        if record[1] is None:
            continue
        if lesson_id is old_lesson_id and tag is not None:
            if 'lesson_tag' not in document:
                document['lesson_tag']=''    
            document['lesson_tag'] = document['lesson_tag'] + '_' +tag
        else:
            document={'lesson_id':lesson_id,'lesson_name':lesson_name, 'lesson_slug':lesson_slug, 'lesson_sub_title':lesson_sub_title, 'lesson_cover_image':lesson_cover_image}
            if tag is not None:
                document['lesson_tag']=tag
        if lesson_id != old_lesson_id and old_lesson_id != -1:
            print 'lesson_id being inserted '+str(old_lesson_id)
            es.create('learnapt', 'lesson',old_document,int(old_lesson_id))
        old_lesson_id=lesson_id
        old_document=document
    print "Converted!\n "
 
if __name__ == "__main__":
    create_item_index()
    create_lesson_index()
    

