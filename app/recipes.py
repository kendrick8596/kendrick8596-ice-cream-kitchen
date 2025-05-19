from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import get_db_connection  # Assuming get_db_connection is in __init__.py or a shared module

recipes_bp = Blueprint('recipes', __name__, url_prefix='/recipes')

@recipes_bp.route('/', methods=['GET', 'POST'])
def submit_recipe():
    if request.method == 'POST':
        if 'user_id' in session:
            account_id = session['user_id']
            recipe_name = request.form['recipe_name']
            prep_time = request.form['prep_time']
            cook_time = request.form['cook_time']
            instructions = request.form['instructions']
            
            conn = get_db_connection()
            cur = conn.cursor()

            # no longer inserting into creators table directly using the logged in users account_id for creator_account_id
            cur.execute(
                "INSERT INTO recipes (recipe_name, prep_time, cook_time, instructions, creator_account_id) VALUES (%s, %s, %s, %s, %s)",
                (recipe_name, prep_time, cook_time, instructions, account_id)
            )
        
            # Commit the transaction and close the connection
            conn.commit()
            cur.close()
            conn.close()
            flash('Recipe submitted successfully!', 'success')
            return redirect(url_for('recipes.success'))
        else:
            flash('You must be logged in to submet a recipe.', 'error')
            return redirect(url_for('auth.login')) # redirect to logon
    
    return render_template('recipe_form.html')

@recipes_bp.route('/success')
def success():
    return render_template('success.html')

@recipes_bp.route('/all')
def view_all_recipes():
    if 'user_id' in session:
        account_id = session['user_id']         # Remove this line, account_id not needed to display all recipes
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, recipe_id FROM recipes")
        all_recipes = cur.fetchall()
        cur.close()
        conn.close()
        print(all_recipes)
        return render_template('all_recipes.html', recipes=all_recipes)
    else:
        return redirect(url_for('auth.login')) # redirect to login if user is not logged in
    
@recipes_bp.route('/my_recipes')
def view_my_recipes():
    if 'user_id' in session:
        account_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url, recipe_id FROM recipes WHERE creator_account_id = %s", (account_id,))
        my_recipes = cur.fetchall()
        cur.close()
        conn.close()
        print(my_recipes) # REMOVE AFTER TESTING
        return render_template('my_recipes.html', recipes=my_recipes)
    else:
        return redirect(url_for('auth.login')) # redirect to login if user is not logged in

@recipes_bp.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if 'user_id' not in session:
        flash('You must be logged in to edit recipes.', 'warning')
        return redirect(url_for('auth.login'))
    
    account_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the recipe details for the given recipe_id and the current user
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url FROM recipes WHERE recipe_id = %s AND creator_account_id = %s", (recipe_id, account_id))
    recipe = cur.fetchone()
    cur.close()
    conn.close()

    if recipe:
        if request.method == 'POST':
            # Handle form submission for editing the recipe
            recipe_name = request.form['recipe_name']
            prep_time = request.form['prep_time']
            cook_time = request.form['cook_time']
            instructions = request.form['instructions']
            image_url = request.form['image_url']           # Need to handle image uploads differently

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE recipes SET recipe_name=%s, prep_time=%s, cook_time=%s, instructions=%s, image_url=%s WHERE recipe_id=%s AND creator_account_id=%s",
                        (recipe_name, prep_time, cook_time, instructions, image_url, recipe_id, account_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('Recipe udpated successfully!', 'success')
            return redirect(url_for('recipes.view_my_recipes'))         # Redirect back to view my_recipes
        
        # If GET request, display edit form
        return render_template('edit_recipe.html', recipe=recipe, recipe_id=recipe_id)
    else:
        flash('Recipe not found or you do not have permissions to edit it.', 'danger')
        return redirect(url_for('recipes.view_my_recipes'))
    
@recipes_bp.route('/view/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url FROM recipes WHERE recipe_id=%s", (recipe_id,))
    recipe = cur.fetchone()
    cur.close()
    conn.close()

    if recipe:
        return render_template('view_recipe.html', recipe=recipe, recipe_id=recipe_id)
    else:
        flash('Recipe not found.', 'warning')
        return redirect(url_for('index'))
    
@recipes_bp.route('/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        flash('You must be logged in to delete recipes.', 'warning')
        return redirect(url_for('auth.login'))
    
    account_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    # checks if recipe belongs to logged in user
    cur.execute("SELECT recipe_id FROM recipes WHERE recipe_id = %s AND creator_account_id = %s", (recipe_id, account_id))
    recipe = cur.fetchone()

    if recipe:
        cur.execute("DELETE FROM recipes WHERE recipe_id=%s AND creator_account_id=%s", (recipe_id, account_id))
        conn.commit()
        cur.close()
        conn.close()
        flash('Recipe deleted successfully', 'success')
    else:
        cur.close()
        conn.close()
        flash('Recipe not found or you do not have permission to delete it.', 'danger')

    return redirect(url_for('recipes.view_my_recipes'))

