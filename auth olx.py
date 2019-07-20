import sqlite3
import pickle
from time import sleep
from bs4 import BeautifulSoup as BS
from selenium import webdriver
# paste your path to geckodriver and data.db
# path_to_geckodriver = r'C:\Users\Alexey\PycharmProjects\OLX Alexey Melnyk\geckodriver.exe'
# path_to_db = r'C:\Users\Alexey\PycharmProjects\OLX Alexey Melnyk\data.sqlite'
path_to_geckodriver = r'geckodriver.exe'
path_to_db = r'data.sqlite'

#info for auth
auth_url = 'https://www.olx.ua/account/?ref%5B0%5D%5Baction%5D=myaccount&ref%5B0%5D%5Bmethod%5D=index'
# xpath_login = '//*[@id="userEmail"]'
# xpath_pass = '//*[@id="userPass"]'
# xpath_submit = '//*[@id="se_userLogin"]'
# xpath_im_not_a_bot = '//*[@id="recaptcha-anchor"]/div[1]'
time_to_wait = 5

#info for items
start_url_dogs = 'https://www.olx.ua/zhivotnye/sobaki/kiev/?search%5Bdistrict_id%5D=11'
start_url_cats = 'https://www.olx.ua/zhivotnye/koshki/kiev/?search%5Bdistrict_id%5D=11'
#its part of url need to go to next mainpage. Click dont work
posturl = '&page='
#max number of items (cats or dogs)
max_num_of_items = 100

def auth(url):
    driver = webdriver.Firefox(executable_path=path_to_geckodriver)
    driver.get(auth_url)
    sleep(3)
    #load cookies ( frow Firefox Windows )
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    sleep(3)
    driver.get(auth_url)

    return driver

def getInfofromStartUrl(url, driver, database):
    page = 1
    #connect cursor of db
    cur = database.cursor()
    #counter
    num_of_items = 0
    #get our mainpage with offers
    driver.get(url)
    #cicle
    while (num_of_items < max_num_of_items):
        #save current url for restore the mainpage with offers
        mainurl = driver.current_url
        soup = BS(driver.page_source, 'html.parser')
        # our links on offers on mainpage
        items = soup.find_all('h3', {'class': 'lheight22 margintop5'})
        for item in items:
            # link of Offer on main page
            link = item.find('a')['href']
            if (url == start_url_dogs):
                pet = 'Dog'
            else:
                pet = 'Cat'

            driver.get(link)
            #soup of our page(from link)
            tmpsoup = BS(driver.page_source, 'html.parser')
            #title of offer
            try:
                nameoffer = tmpsoup.find('div', {'class': 'offer-titlebox'}).find('h1').get_text()
            except:
                if (url == start_url_dogs):
                    nameoffer = 'Dog'
                if (url == start_url_cats):
                    nameoffer = 'Cat'
            #number of offer
            try:
                numberofOffer = tmpsoup.find('div', {'class': 'offer-titlebox'}).find('em').find('small').get_text()
            except:
                numberofOffer = 'none'
            # price
            try:
                price = tmpsoup.find('strong', {'class': 'xxxx-large not-arranged'}).get_text()
            except:
                price = 'contract price'
            #region
            try:
                region = tmpsoup.find('a', {'class':'show-map-link'}).get_text()
            except:
                region = 'none'
            #phone number
            try:
                try:
                    driver.find_element_by_xpath('//*[@id="contact_methods"]/li[2]/div/span').click()
                    sleep(2)
                except Exception as ex:
                    print('cant click on button "Показать". Its normal: ', ex)
                phone = driver.find_element_by_xpath(
                    '/html/body/div[3]/section/div[3]/div/div[1]/div[2]/div/ul[1]/li[2]/div/strong').text
            except:
                phone = 'none'
            num_of_items += 1

            # write to the db
            try:
                #Push our data
                data = [nameoffer, pet, price, region, phone, link, numberofOffer]
                # print(data)
                cur.execute('INSERT INTO pets VALUES(?,?,?,?,?,?,?)', data)
            except Exception as err:
                print('cant push the data:', err)
        #return to main page with links and go to the next
        try:
            page += 1
            mainurl = url + posturl + str(page)
            driver.get(mainurl)
            sleep(5)
            # driver.find_element_by_css_selector('span.fbold:nth-child(18)').click()
        except Exception as ex:
            print('cant click on button "Следующая страница":', ex)
            num_of_items = max_num_of_items
            break
        print('### next mainurl ###')
    database.commit()
    cur.close()

def openDB(path_to_db):
    db = sqlite3.connect(path_to_db)
    cur = db.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS pets( Offer TEXT,'
                                                'Pet TEXT,'
                                                'Price TEXT,'
                                                'Region TEXT,'
                                                'Contacts TEXT,'
                                                'Link TEXT,'
                                                'Numberofoffer TEXT)')
    cur.close()
    db.commit()
    return db

def main():
    driver = auth(auth_url)
    database = openDB(path_to_db)
    try:
        getInfofromStartUrl(start_url_dogs, driver, database)
        getInfofromStartUrl(start_url_cats, driver, database)
    except Exception as ex:
        print('some trouble in getting info:', ex)


    driver.quit()
    database.commit()
    database.close()



if __name__ == '__main__':
    main()



