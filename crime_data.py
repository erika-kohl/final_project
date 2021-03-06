import requests
import json
import sqlite3
import os
import csv
from bs4 import BeautifulSoup
import regex as re

def create_database(db_file):
    '''
    This function takes in a db file and creates the database crime.db which will be used to store all data.
    '''
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_file)
    cur = conn.cursor()
    return cur, conn

def create_state_table(cur,conn,start,end):
    '''
    This function creates the States table and adds it to the database. The States 
    table is created by web scraping from the top 100 safest cities site.
    It uses BeautifulSoup to find the state names and regex to get the abbreviations.
    It assigns the state to a unique primary key id, inserts the abbreviation for 
    each state, and inserts the full name of the state. It has start and end parameters 
    for which rows in the database the data should be added.
    Source: https://www.safehome.org/safest-cities/
    '''
    state = str()
    states = []
    #one request each time it is ran
    state_list_URL = "https://www.safehome.org/safest-cities/"
    page = requests.get(state_list_URL) 
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find("ul" , class_="home-state-list list-unstyled")

    #get state names
    for state in tags:
        state_name = state.text
        states.append(state_name)
    
    #get state abbreviations
    state_abr = []
    pattern = r'cities\/(\w\w)'
    for line in tags:
        new_line = str(line)
        matches =  re.findall(pattern, new_line)
        for match in matches:
            state_abr.append(match.upper())
    
    #insert missing locations 
    states.insert(8, "District of Colombia")
    state_abr.insert(8, "DC")
    states.insert(11, "Hawaii")
    state_abr.insert(11, "HI")
    states.insert(13, "Illinois")
    state_abr.insert(13, "IL")
    
    for i in range(start,end):
        cur.execute("INSERT INTO States (id,abbreviation,state_name) VALUES (?,?,?)",(i,state_abr[i],states[i]))
    conn.commit() 

def create_dangerous_cities_table(cur,conn,start,end):
    '''
    This function creates the Dangerous_Cities table and adds it to the database.
    It uses a website to web scrape the names of the top 100 most dangerous US cities.
    After seperating the city name from the state, it assigns the city to an id and inserts the
    state_id as a foreign key. It has start and end parameters for which rows in the database 
    the data should be added.
    Source: https://www.neighborhoodscout.com/blog/top100dangerous
    '''
    city = str()
    city_list = []
    #one request each time it is ran
    city_list_URL = "https://www.neighborhoodscout.com/blog/top100dangerous"
    page = requests.get(city_list_URL) 
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find_all("h3")
    for location in tags:
        title = location.find("a")
        city_state = title.text
        city_list.append(city_state)

    cityList = []
    stateList = []
    #separate city from state
    for location in city_list:
        separated_location = location.split(", ")
        city = separated_location[0]
        cityList.append(city)
        state = separated_location[1]
        stateList.append(state)

    for i in range(start, end):
        state = stateList[i]
        cur.execute("SELECT id FROM States WHERE abbreviation = ?", (state,))
        state_id = cur.fetchone()[0]
        cur.execute("INSERT INTO Dangerous_Cities (id,city,state_id) VALUES (?,?,?)",(i,cityList[i],state_id))        
    conn.commit()

def create_safe_cities_table(cur, conn, start, end):
    '''
    This function creates the Safe_Cities table and adds it to the database.
    This function uses a website to web scrape the names of the top 100 most safe 
    US cities and adds them to the database. After separating the city name from the state, 
    it assigns the city name an id and inserts the state_id as a foreign key. It has start and 
    end parameters for which rows in the database the data should be added.
    Source: https://www.safehome.org/safest-cities/
    '''
    city = str()
    city_list = []
    #one request each time it is ran
    city_list_URL = "https://www.safehome.org/safest-cities/"
    page = requests.get(city_list_URL) 
    soup = BeautifulSoup(page.content, 'html.parser')
    tags = soup.find_all("h3")
    for location in tags:
        city_state = location.text
        city_list.append(city_state)
        if len(city_list) >= 100:
            break

    cityList = []
    stateList = []
    #separate city from state
    for location in city_list:
        separated_location = location.split(", ")
        city = separated_location[0]
        cityList.append(city)
        state = separated_location[1]
        stateList.append(state)

    for i in range(start, end):
        state = stateList[i]
        cur.execute("SELECT id FROM States WHERE abbreviation = ?", (state,))
        state_id = cur.fetchone()[0]
        cur.execute("INSERT INTO Safe_Cities (id,city,state_id) VALUES (?,?,?)",(i,cityList[i],state_id))        
    conn.commit()

def main():
    '''
    This function sets up the database and creates the entire States, Safe_Cities, and Dangerous_Cities 
    tables using create_database(db_file), create_state_table(cur, conn, start, end), 
    create_dangerous_cities_table(cur, conn, start, end), and create_safe_cities_table(cur, conn, start, end),
    while limiting stored data to at most 25 rows at a time.
    '''
    #setup database
    cur, conn = create_database('crime.db')
    
    #create State table if not exists
    cur.execute("CREATE TABLE IF NOT EXISTS States (id INTEGER PRIMARY KEY, abbreviation TEXT , state_name TEXT)")

    cur.execute('SELECT COUNT(*) FROM States')
    state_row_count = cur.fetchone()[0]
    
    if state_row_count == 0:
        print("Collecting States and State Abbreviations...(1/3)")
        create_state_table(cur,conn,0,22)
        print("Finished")
    
    elif state_row_count == 22:
        print("Collecting States and State Abbreviations...(2/3)")
        create_state_table(cur,conn,22,40)
        print("Finished")
    
    elif state_row_count == 40:
        print("Collecting States and State Abbreviations...(3/3)")
        create_state_table(cur,conn,40,51)
        print("States table is Completed.")

    if state_row_count == 51:
        #create Safe_Cities table if not exists
        cur.execute("CREATE TABLE IF NOT EXISTS Safe_Cities (id INTEGER PRIMARY KEY, city TEXT, state_id INTEGER)")
        #create Dangerous_Cities table if not exists
        cur.execute("CREATE TABLE IF NOT EXISTS Dangerous_Cities (id INTEGER PRIMARY KEY, city TEXT, state_id INTEGER)")
    
        #limiting amount of data collected to 25 rows each time file is ran
        cur.execute('SELECT COUNT(*) FROM Safe_Cities')
        safe_row_count = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM Dangerous_Cities')
        danger_row_count = cur.fetchone()[0]
    
        if safe_row_count == 0 and danger_row_count == 0:
            print("Collecting Web Data...(1/4)")
            create_safe_cities_table(cur,conn,0,25)
            create_dangerous_cities_table(cur,conn,0,25)
            print("Finished")

        elif safe_row_count == 25 and danger_row_count == 25:
            print("Collecting Web Data...(2/4)")
            create_safe_cities_table(cur,conn,25,50)
            create_dangerous_cities_table(cur,conn,25,50)
            print("Finished")

        elif safe_row_count == 50 and danger_row_count == 50:
            print("Collecting Web Data...(3/4)")
            create_safe_cities_table(cur,conn,50,75)
            create_dangerous_cities_table(cur,conn,50,75)
            print("Finished")

        elif safe_row_count == 75 and danger_row_count == 75:
            print("Collecting Web Data...(4/4)")
            create_safe_cities_table(cur,conn,75,100)
            create_dangerous_cities_table(cur,conn,75,100)
            print("Safe_Cities and Dangerous_Cities tables are Completed.")

        elif safe_row_count == 100 and danger_row_count == 100:
            print("All 100 rows of Web Data have been inserted into the Safe_Cities and Dangerous_Cities tables in the database.")
 
if __name__ == "__main__":
    main()