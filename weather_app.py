from flask import Flask,render_template,request
import requests
import datetime
from datetime import datetime
import sqlite3
from sqlite3 import Error

#flask object
app = Flask(__name__,template_folder="template",static_folder="static")

def check_records(records):
    #to check timestamp updated within 24 hrs using check_update function return day         
    day_diff=check_update(records[3])
    return check_day(day_diff)

#within 24hrs
def check_day(day_diff):
    #if day is exist
    if day_diff:
        return True   
    #if day is not exist 
    else :
        return False

#To different between timestamp in database and now timestamp and return days
def check_update(time):
    datetime_in_db = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
    now_datetime=datetime.now()
    day_diff=now_datetime-datetime_in_db
    secs = day_diff.total_seconds()
    day=int((secs / 3600)/24)
    return day

#To convert kelvin to celcius
def tocelcius_tofahrenheit(temp):
    celcisus_temp=round(float(temp) - 273.16,2)
    fahrenheit_temp = round(float(celcisus_temp * ( 9 / 5 ) + 32))
    return [fahrenheit_temp,celcisus_temp]

#connect to sqlite connection
def connect_db(city):    
    try:
        sqliteConnection = sqlite3.connect('weather.db')
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")  
        cursor.execute("CREATE TABLE IF NOT EXISTS weather_details(city text, description text, temp integer, weatherTime real)")
        sqliteConnection.commit()
        print("Created Table Successfully")
        return sqliteConnection
    except sqlite3.Error as error:
        print("Failed to connect sqlite connection", error)

#update weather details into table
def update_db(sqliteConnection,update_record):
            cursor = sqliteConnection.cursor()
            sql_update_query = """Update weather_details set description =?,temp=?,weatherTime=? where city = ?"""
            cursor.execute(sql_update_query,(update_record[1],update_record[2],update_record[3],update_record[0]))
            sqliteConnection.commit()
            print("Record Updated Successfully ") 

#insert new weather details into table
def insert_db(sqliteConnection,insert_record):
        cursor = sqliteConnection.cursor()
        sql_insert_query="""INSERT INTO weather_details(city,description,temp,weatherTime) VALUES(?, ?, ?, ?)"""
        cursor.execute(sql_insert_query, insert_record)
        sqliteConnection.commit()
        print("Record Inserted Successfully")
    
# function to get records from table based on location     
def get_records(sqliteConnection,city):
    cursor = sqliteConnection.cursor()
    #to select records from  tabel based on city
    sqlite_select_query = """SELECT * from weather_details where city=?"""
    cursor.execute(sqlite_select_query,[city])
    records= cursor.fetchall()
    
    #if records exists
    if len(records):
        for elements in records:
            records=list(elements)
        day_exist=check_records(records)
        #if day exist
        if day_exist:
            #to get current weather details using function 
            update_record=get_weather(city)
            update_db(sqliteConnection,update_record)
            return update_record
        #not exist
        else:
            print("Exist record  display Successfully")
            return records
    #if city is not exist
    else:
        #get weather details 
        insert_record=get_weather(city)
        insert_db(sqliteConnection,insert_record)
        return insert_record

      
#to get location weather detail in url
def get_weather(city):
    url="http://api.openweathermap.org/data/2.5/weather?q="+city+"&appid=1f36ce553bcc503168e616137464eae1"
    json_response=requests.get(url).json()
    weather_description=json_response["weather"][0]["description"]
    temp=json_response["main"]["temp"]
    time=datetime.now()
    return [city,weather_description,temp,time]

@app.route("/")
def index():
    error = None
    return render_template("search.html",error=error)

@app.route("/result",methods =['POST', 'GET'])
def weather():
 try:
    if request.method == 'POST':
        location = request.form['city'].lower()

        #connect sqlite
        sqliteConnection=connect_db(location)
        #get records from table based on location
        record=get_records(sqliteConnection,location)
        #get celcius value
        temp=tocelcius_tofahrenheit(record[2])
        #print records
        print({"city":record[0],"Weather description":record[1],"temp(in F)":temp[0],"temp(in C)":temp[1]})
        return render_template('weather.html',city=record[0],description=record[1],tempk=temp[0],tempc=temp[1],time=record[3]) 
   
 except requests.exceptions.ConnectionError:
      print("No network connection")
      error="No network connection.Try again!!!!"
      return render_template('search.html',error=error)
      #return " <body style = \"background-color:#141414;text-align:center\"> <h3 style = \"color: whitesmoke\"> City name is not found<h3> <a href=\"/\">Click here to Back Home</a></body>"
 except KeyError:
      print("Invalid city name")
      error="Invalid city name.Try again!!!!"
      return render_template('search.html',error=error)

if __name__ == '__main__':
   app.run(debug = True)
