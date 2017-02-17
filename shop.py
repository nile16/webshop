from flask import Flask, request
from flask_cors import CORS #Used to allow http requsets from other servers than the one this code runs on
import MySQLdb #Used to communicate with MySQL database
import json #Used to format data to JSON format
from configparser import SafeConfigParser #Used to read database user and password from .ini file
import time

config = SafeConfigParser()
config.read('databaseconfig.ini')


app = Flask(__name__)
CORS(app)

#    CREATE TABLE `Order`        ( `order_id` int(11) NOT NULL AUTO_INCREMENT, `customer_id` int(11), `time` int(11), PRIMARY KEY (`order_id`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
#    CREATE TABLE `OrderProduct` ( `product_id` int(11), `order_id` int(11) ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


@app.route('/order',methods = ['POST'])
def order():
    received_data=json.loads(request.get_data())
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Customer WHERE email='"+received_data['user']+"' AND password='"+received_data['passwd']+"';")
    result=cursor.fetchall()
    if (len(result)!=1):
        return("error")
    else:
        cursor = db.cursor()
        cursor.execute("INSERT INTO `Order` (customer_id,time) VALUES ("+str(result[0][0])+","+str(time.time())+");")
        for item in received_data['list']:
            cursor.execute("INSERT INTO OrderProduct ( product_id, order_id ) VALUES ("+str(item[0])+",LAST_INSERT_ID());")
            cursor.execute("UPDATE Product SET instock=instock-1 WHERE product_id='"+str(item[0])+"';")
        db.commit()
        db.close()
        return("ok")

@app.route('/addstock',methods = ['POST'])
def addstock():
    received_data=json.loads(request.get_data())
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("INSERT INTO Product ( product_id, name, description, imgname, manufacturer, instock, cost ) VALUES ("+str(received_data[0])+",'"+received_data[1]+"','"+received_data[2]+"','"+received_data[3]+"','"+received_data[4]+"',"+str(received_data[5])+","+str(received_data[6])+");")
    db.commit()
    db.close()
    return("ok")

@app.route('/signup',methods = ['POST'])
def signup():
    print(request.get_data())
    return("ok")

@app.route('/updatestock',methods = ['POST'])
def updatestock():
    received_data=json.loads(request.get_data())
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("UPDATE Product SET name='"+received_data[1]+"', description='"+received_data[2]+"', imgname='"+received_data[3]+"', manufacturer='"+received_data[4]+"', instock=instock+"+str(received_data[5])+", cost="+str(received_data[6])+" WHERE product_id="+str(received_data[0])+";")
    db.commit()
    db.close()
    return("ok")

@app.route('/removestock',methods = ['POST'])
def removestock():
    received_data=json.loads(request.get_data())
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("DELETE FROM Product WHERE product_id="+str(received_data)+";")
    db.commit()
    db.close()
    return("ok")

@app.route('/listorders')
def listorders():
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM `Order` INNER JOIN `Customer` USING (customer_id);")
    buyers=cursor.fetchall()
    y=[]
    for buyer in buyers:
        x=[]
        x.append(str(buyer[0]))            #customer_id
        x.append(str(buyer[1]))            #order_id
        x.append(str(buyer[2]))            #UNIX timestamp
        x.append(buyer[3].encode('utf-8')) #First Name
        x.append(buyer[4].encode('utf-8')) #Last Name
        x.append(buyer[5].encode('utf-8')) #ssn
        x.append(buyer[6].encode('utf-8')) #address
        x.append(buyer[7].encode('utf-8')) #city
        x.append(buyer[8].encode('utf-8')) #email
        x.append(buyer[9].encode('utf-8')) #phone
        cursor.execute("SELECT * FROM `OrderProduct` INNER JOIN `Product` USING (product_id) WHERE order_id="+str(buyer[1])+";")
        items=cursor.fetchall()
        z=[]
        for item in items:
            z.append([str(item[0]),item[2].encode('utf-8'),item[5].encode('utf-8'),str(item[7])])    
        x.append(z)
        y.append(x)
    db.commit()
    db.close()
    return(json.dumps(y))

@app.route('/search',methods = ['POST'])
def search():
    received_data=request.get_data()
    if (received_data=="top10"):
	    query="SELECT Product.* FROM Product INNER JOIN OrderProduct USING (product_id) GROUP BY Product.product_id ORDER BY count(*) DESC LIMIT 10;"
    else:
        words=received_data.split()
        query="SELECT * FROM Product"
        if len(words)>0:
            query+=" WHERE ( "
            for y in range(len(words)):
                query+="( name LIKE '%"+words[y]+"%' OR description LIKE '%"+words[y]+"%' OR manufacturer LIKE '%"+words[y]+"%') "
                if y!=len(words)-1:
                    query+=" AND "
            query+=" )"
    db = MySQLdb.connect(host=config.get('main', 'host'), user=config.get('main', 'user'), passwd=config.get('main', 'passwd'), db='webshop', use_unicode=True, charset="utf8")
    cursor = db.cursor()
    cursor.execute(query)
    result=cursor.fetchall()
    y=[]
    for data in result:
        x=[]
        x.append(str(data[0]))            #productID
        x.append(data[1].encode('utf-8')) #Name
        x.append(data[2].encode('utf-8')) #Description
        x.append(data[3].encode('utf-8')) #imgname
        x.append(data[4].encode('utf-8')) #manufacturer
        x.append(str(data[5]))            #instock
        x.append(str(data[6]))            #cost
        y.append(x)
    return(json.dumps(y))

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=1204)
