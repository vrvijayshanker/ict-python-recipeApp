import bcrypt
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

# Database connection part -------------------------------
import mysql.connector

mydb = mysql.connector.connect( # mydb can be any name
    host = 'localhost',
    user = 'root',
    password = 'password',
    database = 'recipedb'
)

# -----------------------------------------------------------

# DB Functions -----------------------------------------------

# Function to get all recipes
def getAllRecipes():
    cursor = mydb.cursor()
    cursor.execute("select * from recipes")
    recipe_rows = cursor.fetchall()
    return recipe_rows

# Function to get recipes based on category
def getRecipeByCategory(category):
  cursor = mydb.cursor()
  cursor.execute("SELECT * FROM recipes WHERE category = %s", (category,))
  category_recipes = cursor.fetchall()
  return category_recipes

# Functon to add a user
def addNewUser(user_name, email, password):
  cursor = mydb.cursor()
  sql = "INSERT INTO users (user_name, email, password) VALUES (%s, %s, %s)"
  data = (user_name, email, password)

  try:
    cursor.execute(sql, data)
    mydb.commit()
    return True
  except mysql.connector.Error as err:
    print(f"Error inserting user: {err}")
    return False

# Function to get all users
def getAllUsers():
    cursor = mydb.cursor()
    cursor.execute("select * from users")
    alluser_rows = cursor.fetchall()
    return alluser_rows

# To find a user by ID
def findUserById(id):
    cursor = mydb.cursor()
    cursor.execute("select * from users where user_id = %s", (id,))
    singleuser = cursor.fetchone()
    return singleuser

def getComments(recipeId):
  cursor = mydb.cursor()
  cursor.execute("select * from comments where recipe_id = %s", ((recipeId,)))
  comments = cursor.fetchall()
  if comments:
     return comments
  else:
    return f"comments empty"

def getUserName(user_id):
  cursor = mydb.cursor()
  cursor.execute("select user_id, user_name from users where user_id = %s", (user_id,))
  username = cursor.fetchone()
  return username

def addComment(uid, rec_id, comment):
  cursor = mydb.cursor()
  sql = "INSERT INTO comments (user_id, recipe_id, user_comment) VALUES ( %s, %s, %s)"
  data = (uid, rec_id, comment)
  try:
    cursor.execute(sql, data)
    mydb.commit()
    return True
  except mysql.connector.Error as err:
    print(f"Error Adding comment {err}")
    return False

# Function to handle login
def handleLogin(u_email):
  cursor = mydb.cursor()
  sql = "SELECT * FROM users where email=%s"
  cursor.execute(sql, (u_email,)) #LOGIN PROBLEM WAS HERE, PASS AS A TUPLE INSTEAD OF STR
  user_rows = cursor.fetchone()
  return user_rows

def getOneRecipe(recipeId):
  cursor = mydb.cursor()
  cursor.execute("select * from recipes where recipe_id = %s", (recipeId,))
  onerecipe = cursor.fetchone()
  print(onerecipe)
  return onerecipe

  
  
# /DB Functions --------------------------------------------

app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = 'your_secret_key'


@app.route('/', methods=['GET', 'POST'])
def index():
  # message = request.args.get('message')
  if request.method == 'GET':
    return render_template('index.html')

  elif request.method == 'POST':
      try:
            entered_email = request.form['user_email']
            entered_password = request.form['user_password']
            encoded_password = entered_password.encode('utf-8')
            db_data = handleLogin(entered_email)
            db_hash_password_bytes = db_data[3] # Here we don't know what db_data[4] type is so
            db_hash_password = db_hash_password_bytes.encode('utf-8') # we encode it. This is assuming the database stores UTF-8 encoded hash

            if db_data:
              db_user_id = db_data[0]

              if bcrypt.checkpw(encoded_password, db_hash_password):
                # message = "Passwords match"
                session['user_id'] = db_user_id
                print('\n\n'+str(db_user_id)+'\n\n')

                if 'user_id' not in session:
                  return render_template('index.html')
                else:  
                  return redirect(url_for('userdashboard', data=db_data, user_id = db_user_id)) # Redirect to user dash
                
              else:
                message = "Not match"
                return redirect(url_for('index', message=message))
      except KeyError as e:
            return f"Missing form field: {e}", 400
        


    
@app.route('/allrecipes', methods=['GET', 'POST'])
def allrecipe():
  all_recipes = getAllRecipes()  # get all the data from function to var
  return render_template('allrecipes.html', data=all_recipes) # returns page with data passed to it.


@app.route('/categoryrecipes')
def get_recipes():
    category = request.args.get('category')  # Get the selected category
    if category == 'All':
       # select all
       recipes = getAllRecipes()
    else:
       # select based on category
       recipes = getRecipeByCategory(category)
    return jsonify(recipes)





@app.route('/register', methods = ['GET', 'POST'])
def register():  
  if request.method == 'GET':
    return render_template('register.html')
  
  elif request.method == 'POST':
    user_name = request.form['user_name']
    email = request.form['email']
    password = request.form['password'] # should hash the password before storing
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    success = addNewUser(user_name, email, hashed)
    mydb.close()

    if success:
      message = "Registration successful!"
      return redirect(url_for('index', message=message))  # Redirect to homepage

    else:
      message = "Error during registration."
      return render_template('registration.html', message=message)
    
@app.route('/addnewrecipe')
def addnewrecipe():
   pass
  #  recipe_name = request.form['recipe_name']
  #  ingredients = request.form['ingredients']
  #  instructions = request.form['instructions']
  #  duration = request.form['duration']
  #  servings = request.form['servings']
  #  recipe_name = request.form['recipe_name']
    


@app.route('/single_recipe/<int:recipe_id>', methods = ['GET', 'POST'])
def single_recipe(recipe_id):
    
    if request.method == 'GET':
      recipe_data = getOneRecipe(recipe_id)
      comments_data = getComments(recipe_id)
      if comments_data:
          comments_with_usernames = []
          for comment in comments_data:
            user_id = comment[0]
            user_info = getUserName((user_id,))

            print(user_id)

            combined_comment = {
                "user_id": user_id,
                "recipe_id": comment[1],
                "comment": comment[2],
                "user_name": user_info[1]
            }
            comments_with_usernames.append(combined_comment)
      else:
          # No comments found, set a message
          comments_with_usernames = "NO COMMENTS YET"
            
        
      
      return render_template('single_recipe.html', recipe_data=recipe_data, comments_data=comments_with_usernames) 

    if request.method == 'POST':
      comment_text = request.form.get('usercomment')
      form_user_id = request.form.get('user_id') # But this is not login person id here!
      form_recipe_id = request.form.get('recipe_id')
      success = addComment(form_user_id, form_recipe_id, comment_text)

      #WORKS BUT BE ALERT ON uid and recipeid
      if success:
        return redirect(url_for('single_recipe', recipe_id=recipe_id, comment_added="Your comment has been added!"))
      else:
        return redirect(url_for('single_recipe', recipe_id=recipe_id, comment_added="Error in adding comment!"))
    

    # return render_template('single_recipe.html', recipe_data=recipe_data, comments_data=comments_with_usernames)
    # recipes = getOneRecipe(recipe_id)

    # if recipes:
    #     return render_template('single_recipe.html', recipedata=recipes)
    # else:
    #     return "Recipe not found"


@app.route('/userdashboard/<int:user_id>')
def userdashboard(user_id):
  if 'user_id' not in session:
    message = "Not logged in"
    return redirect(url_for('index', message=message))
  else:
    db_data = findUserById(user_id)  
    return render_template('userdashboard.html', data=db_data)
  
  


@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('index'))


if __name__ == '__main__':
  app.run(debug=True)
