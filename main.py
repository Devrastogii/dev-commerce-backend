from flask import Flask, request
from flask_cors import CORS
import pandas as pd
import json
import numpy as np
import pickle

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

@app.route("/")
def home():    
    return "HI"

@app.route("/sale_products_show")
def sale():    
    sales_data =  pd.read_csv('backend/csv/sale.csv')    

    sales_data['description'] = sales_data['description'].apply(lambda x: x.replace('[', ''))
    sales_data['description'] = sales_data['description'].apply(lambda x: x.replace(']', ''))   
    sales_data['description'] = sales_data['description'].apply(lambda x: x.split(","))  
                
    export_dict = {
    'uid': list(sales_data['u_id']),
    'name': list(sales_data['name']),
    'offer': list(sales_data['offer_price']),
    'original': list(sales_data['original_price']), 
    'off': list(sales_data['off_now']), 
    'total_ratings': list(sales_data['total_ratings']), 
    'rating': list(sales_data['rating']),    
    'description': list(sales_data['description'])
    }
    
    return json.dumps(export_dict)

@app.route('/frequently_purchased')
def frequently_purchased():
    data =  pd.read_csv('backend/csv/frequent.csv')    
        
    data['total_ratings'] = sorted(list(data['total_ratings']), reverse=True) 

    data['description'] = data['description'].apply(lambda x: x.replace('[', ''))
    data['description'] = data['description'].apply(lambda x: x.replace(']', ''))   
    data['description'] = data['description'].apply(lambda x: x.split(",")) 

    export_dict = {
    'uid': list(data['u_id']),
    'name': list(data['name']),
    'offer': list(data['offer_price']),
    'original': list(data['original_price']), 
    'off': list(data['off_now']), 
    'total_ratings': list(data['total_ratings']), 
    'rating': list(data['rating']),
    'description': list(data['description'])
    }
    
    return json.dumps(export_dict)

whichProductToShow = 0

@app.route('/products_show', methods = ["POST"])
def productShow():
    if request.method == "POST":
        whichProductToShow = request.get_json()       
               
        category = ['result_mobiles', 'result_monitors', 'result_watch', 'result_laptops', 'result_tablets', 'result_fridge', 'result_machine', 'result_purifier', 'sale']        

        productID = whichProductToShow['id']
      
        data =  pd.read_csv(f'backend/csv/{category[productID]}.csv')                         

        data.drop(columns='Unnamed: 0', inplace=True)
        data['off_now'] = data['off_now'].apply(lambda x: x.replace('off', ''))
        data['off_now'] = data['off_now'].apply(lambda x: x.replace('%', ''))
        data['off_now'] = data['off_now'].apply(lambda x: int(x))

        data['description'] = data['description'].apply(lambda x: x.replace('[', ''))
        data['description'] = data['description'].apply(lambda x: x.replace(']', ''))
        data['description'] = data['description'].apply(lambda x: x.split(","))                                        

        export_dict = {
            'name': list(data['name']),
            'offer': list(data['offer_price']),
            'original': list(data['original_price']), 
            'off': list(data['off_now']), 
            'total_ratings': list(data['total_ratings']), 
            'rating': list(data['rating']),
            'description': list(data['description']),
            'uid': list(data['u_id']),           
        }              
        
        return json.dumps(export_dict)
    
def readPKL(id):
    recommendList = ['mobile', 'monitor', 'watch', 'laptop', 'tablet', 'fridge', 'machine', 'purifier', 'sale', 'frequent']
    recommend = pickle.load(open(f'backend/recommend/recommend_{recommendList[id]}.pkl', 'rb'))
    similarity = pickle.load(open(f'backend/similarity/similarity_{recommendList[id]}.pkl', 'rb'))
    
    return recommend, similarity
    
@app.route('/product-recommend', methods = ['POST'])
def productRecommend():
    if request.method == "POST":
        data = request.get_json()
        name = request.get_json()
        catId = data.get('id')      

        recommend, similarity = readPKL(catId)

        productName = []
        productOffer = []
        productPrice = []
        productDescription = []
        productOff = []
        productTotalRating = []
        productRating = []     
        productId = []  

        recommend['description_x'] = recommend['description_x'].apply(lambda x: x.replace('[', ''))
        recommend['description_x'] = recommend['description_x'].apply(lambda x: x.replace(']', ''))
        recommend['description_x'] = recommend['description_x'].apply(lambda x: x.split(","))   

        recommend['off_now'] = recommend['off_now'].apply(lambda x: x.replace("off", ""))            
        recommend['off_now'] = recommend['off_now'].apply(lambda x: x.replace("%", ""))                    
        recommend['off_now'] = recommend['off_now'].apply(lambda x: x.replace(" ", ""))                

        def recommendProduct(name):
            product_index = recommend[recommend['name_x'] == name['name']].index[0]
            distances = similarity[product_index]    
            sorted_indices = sorted(list(enumerate(distances)), reverse = True, key = lambda x: x[1])
            filtered_indices = [sorted_indices[0]]
            for i in range(1, len(sorted_indices)):
                if sorted_indices[i][1] != sorted_indices[i - 1][1]:
                    filtered_indices.append(sorted_indices[i])
    
            for i in filtered_indices[1:50]:
                productName.append(recommend.iloc[i[0]]['name_x'])
                productOffer.append(recommend.iloc[i[0]]['offer_price'])
                productPrice.append(recommend.iloc[i[0]]['original_price'])
                productOff.append(recommend.iloc[i[0]]['off_now'])
                productTotalRating.append(recommend.iloc[i[0]]['total_ratings'])
                productRating.append(recommend.iloc[i[0]]['rating'])
                productDescription.append(recommend.iloc[i[0]]['description_x'])
                productId.append(recommend.iloc[i[0]]['u_id'])

        recommendProduct(name)

        productOffer = [str(offer) for offer in productOffer]
        productPrice = [str(price) for price in productPrice]
        productOff = [str(off) for off in productOff]
        productTotalRating = [str(total_rating) for total_rating in productTotalRating]
        productRating = [str(rating) for rating in productRating]        

        export_dict = {
            'name': productName,
            'offer': productOffer,
            'original': productPrice, 
            'off': productOff, 
            'total_ratings': productTotalRating, 
            'rating': productRating,
            'description': productDescription,         
            'uid': productId        
        }              
        
        return json.dumps(export_dict) # any col should not be integer type as json only takes str values so convert numerical col in str

app.run(debug=True)