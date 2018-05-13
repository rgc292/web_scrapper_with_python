from flask import Flask, render_template, request
from bs4 import BeautifulSoup, Comment
from urllib.request import urlopen
import urllib
import re
import os
import json

######################################################################
# My Functions #######################################################
######################################################################

def get_data(url_to_scrape): # get data from webpage and return the data as a list
    data = urlopen(url_to_scrape)

    if data.getcode() == 200:
        soup = BeautifulSoup(data, "html.parser")
        summary = soup.find_all("div", class_="minibubble template hide") #Get all div with class 'minibubble template hide' 
        summary_content = [str(div.find(string=lambda text:isinstance(text,Comment))) for div in summary] # Gather content available as a comment with a key called flexData and without it
        summary_content_as_dictionary_without_flexdata = [json.loads(value) if value != '' else None for value in summary_content if 'flexdata' not in value.lower()] #Filter content with no flexData converting it into dictionaries
        summary_content_with_flexdata_removed = [json.loads((value.split(',"flexData"', 1)[0]+'}')) if value != '' else None for value in summary_content if 'flexdata' in value.lower()] #Filter content with flexData removing the flexData and converting it into dictionaries
        summary_content_as_dictionary_without_flexdata.extend(summary_content_with_flexdata_removed) #Merge contents that had and did not have flexData

        picture = soup.find_all("div", class_="zsg-photo-card-img") #Get all div with class 'zsg-photo-card-img'
        picture_cleaned = [link.find('img') for link in picture] #Filter the 'img' tag
        picture_cleaned_link = [str(link).split('"')[1]  if (link != '' and 'p_e/' in str(link)) else None for link in picture_cleaned] #Filter each url to image when neither the url is empty nor 'p_e/' is present

        cleaned_content = [['bed','bath','sqft','price','price','is empty lot?','image','link']] #Store on a list the list of headings to be used on a table on the view

        for value in summary_content_as_dictionary_without_flexdata: #Go over the list of dictionaries fishing each content's key
            bed = value['bed']
            sqft = value['sqft']
            bath = value['bath']
            price1 = value['label']
            price2 = value['title']
            is_empty_lot = str(value['isPropertyTypeVacantLand'])
            image = value['image'].replace('\\','') #Get the link to the image to be displayed to the user as clicable
            
            if str(is_empty_lot) == '':
                is_empty_lot = None

            if str(image) == '':
                image = 'null'

            link = '#'
            for picture_link in picture_cleaned_link: #Guarantee the match between clickable image and link to display the large image
                if (str(image) != 'null' and str(picture_link) != 'None'):
                    if str(picture_link).split('p_e/')[1].lower() == str(image).split('p_a/')[1].lower():
                        link = str(picture_link)
                else:
                    link = link
                    image = image

            bed = convert_feature_into_float(bed)
            sqft = convert_feature_into_float(sqft)
            bath = convert_feature_into_float(bath)
            price1 = convert_price_into_float(price1)
            price2 = convert_price_into_float(price2)

            cleaned_content.append([bed,bath,sqft,price1,price2,is_empty_lot,image,link])

        return cleaned_content

    else:
        return 'status_code_not_200'


def convert_price_into_float(price): # convert the numerical string data from prices into float
    price = str(price).replace('$', '')

    try:
	    if 'k' in price.lower():
	        price = price.lower()
	        price = price.replace('k','')
	        price = float(price) * 1000
	        return price
	    
	    elif 'm' in price.lower():
	        price = price.lower()
	        price = price.replace('m','')
	        price = float(price) * 1000000
	        return price

    except (AttributeError, TypeError):
        return None


def convert_feature_into_float(feature): # convert the numerical string data from non prices into float
    try:
        return float(feature)

    except (AttributeError, TypeError):
        return None


def save_data_to_file(data): # save the data from list to file
	if os.path.isfile('./data.dat'):
		write_to_file('./data.tmp','w+',data)
		replace_old_file('./data.tmp','./data.dat')

	else:
	    write_to_file('data.dat','w+')


def write_to_file(file_name,mode,data): # open file to save list content
	file = open(file_name,mode)
	
	for value in data:
		file.write(str(value[0])+','+str(value[1])+','+str(value[2])+','+str(value[3])+','+str(value[4])+','+str(value[5])+','+str(value[6])+','+str(value[7])+'\n')
	file.close()

    
def replace_old_file(new_file,old_file): # replace content of temporary file into permanent file
    os.replace(new_file,old_file)


#######################################################################
# My Program ##########################################################
#######################################################################

app = Flask(__name__)
title  = "Enter the zip code from which Zillow's on sale property data must be collected:" 
subtitle = 'Zip Code'
try_another_zip_code = 'This zip code is not allowed! Try a different one!'
zip_code = ''
url_to_scrape = ''


@app.route('/')
def homepage(): # render initial homepage
    return render_template('index.html', title = title, subtitle = subtitle)


@app.route('/', methods=['GET','POST'])
def get_zip_code(): # render homepage scrapped contents based on user input zip code up to 27 rows
    if request.method == 'POST':
        global data_to_display
        
        print("I got it!")

        zip_code = request.form['zip_code']
        
        try:
            int(zip_code)
            print(zip_code)
            url_to_scrape = "https://www.zillow.com/homes/for_sale/"+str(zip_code)+"_rb/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy"
            data_to_display = get_data(url_to_scrape)

            if data_to_display != 'status_code_not_200':
                save_data_to_file(data_to_display)
                count_data_to_display = len(data_to_display) - 1
                return render_template('index.html', title = title, subtitle = subtitle, data_to_display = data_to_display, count_data_to_display = count_data_to_display)

            else:
                return render_template('index.html', title = title, subtitle = subtitle, try_another_zip_code = try_another_zip_code) 

        except ValueError:
            print('Not working')
            return render_template('index.html', title = title, subtitle = subtitle, try_another_zip_code = try_another_zip_code)

        except (NameError,urllib.error.URLError):
            print('Not working')
            return render_template('index.html', title = title, subtitle = subtitle, try_another_zip_code = 'Your internet connection or used URL is not working!')            

    else:
        return render_template('index.html', title = title, subtitle = subtitle)

if __name__ == '__main__':
    app.run()