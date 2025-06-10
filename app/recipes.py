from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import get_db_connection  # Assuming get_db_connection is in __init__.py or a shared module
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
import os
import uuid

recipes_bp = Blueprint('recipes', __name__, url_prefix='/recipes')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'recipes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions for allowed file types
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@recipes_bp.route('/', methods=['GET', 'POST'])
@login_required
def submit_recipe():
    if request.method == 'POST':
        account_id = current_user.id
        recipe_name = request.form['recipe_name']
        prep_time = request.form['prep_time']
        cook_time = request.form['cook_time']
        
        # --- NEW PROCESSING FOR INGREDIENTS AND INSTRUCTIONS ---
        # Ingredients: Split by newlines, strip whitespace, join with ', ' for consistent storage
        instructions_raw = request.form.get('instructions')
        if instructions_raw:
            instructions = "\n".join([step.strip() for step in instructions_raw.split('\n') if step.strip()])
        else:
            instructions = None

        description = request.form.get('description')

        ingredients_raw = request.form.get('ingredients')
        if ingredients_raw:
            ingredients = ", ".join([item.strip() for item in ingredients_raw.split('\n') if item.strip()])
        else:
            ingredients = None  # Or an empty string if db expects it

        image_url_for_db = None # Initialized to None

        # Process File Upload
        if 'recipe_image' in request.files:
            image_file = request.files['recipe_image']

            if image_file.filename == '':
                pass # No file selected, image_url_for_db remains None
            elif image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                full_image_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                try:
                    image_file.save(full_image_path)
                    # Path relative to the 'static' folder for URL generation
                    image_url_for_db = os.path.join('uploads', 'recipes', unique_filename).replace('\\', '/')
                except Exception as e:
                    flash(f'Failed to save image: {e}', 'error')
                    return redirect(url_for('recipes.submit_recipe'))
            else:
                flash('Invalid image file type. Please upload a JPG, PNG, or GIF.', 'error')
                return redirect(url_for('recipes.submit_recipe'))
        
        # Insert into database
        conn = get_db_connection()
        cur = conn.cursor()

        # no longer inserting into creators table directly using the logged in users account_id for creator_account_id
        cur.execute(
            "INSERT INTO recipes (recipe_name, prep_time, cook_time, instructions, description, ingredients, image_url, creator_account_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (recipe_name, prep_time, cook_time, instructions, description, ingredients, image_url_for_db, account_id)
        )
    
        # Commit the transaction and close the connection
        conn.commit()
        cur.close()
        conn.close()
        flash('Recipe submitted successfully!', 'success')
        return redirect(url_for('recipes.success'))

    return render_template('recipe_form.html')

@recipes_bp.route('/success')
def success():
    return render_template('success.html')

@recipes_bp.route('/all')
def view_all_recipes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, recipe_id, image_url FROM recipes")
    all_recipes = cur.fetchall()
    cur.close()
    conn.close()
    print(all_recipes)
    return render_template('all_recipes.html', recipes=all_recipes)

    
@recipes_bp.route('/my_recipes')
@login_required
def view_my_recipes():
    account_id = current_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url, recipe_id FROM recipes WHERE creator_account_id = %s", (account_id,))
    my_recipes = cur.fetchall()
    cur.close()
    conn.close()
    print(my_recipes) # REMOVE AFTER TESTING
    return render_template('my_recipes.html', recipes=my_recipes)

@recipes_bp.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    account_id = current_user.id 
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the recipe details for the given recipe_id and the current user
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url, description, ingredients FROM recipes WHERE recipe_id = %s AND creator_account_id = %s", (recipe_id, account_id))
    recipe = cur.fetchone()
    cur.close()
    conn.close()

    if recipe:
        if request.method == 'POST':
            # Handle form submission for editing the recipe
            recipe_name = request.form['recipe_name']
            prep_time = request.form['prep_time']
            cook_time = request.form['cook_time']

            instructions_raw = request.form['instructions']
            if instructions_raw:
                instructions = "\n".join([step.strip() for step in instructions_raw.split('\n') if step.strip()])
            else:
                instructions = None

            description = request.form.get('description')

            ingredients_raw = request.form.get('ingredients')
            if ingredients_raw:
                ingredients = ", ".join([item.strip() for item in ingredients_raw.split('\n') if item.strip()])
            else:
                ingredients = None  # Or an empty string if db expects it

            # Start with existing image_url from database in this case indexed at 4
            new_image_url_for_db = recipe[4]

            # Handle Image upload/update for edit
            if 'recipe_image' in request.files:
                image_file = request.files['recipe_image']

                if image_file.filename == '':
                    pass # No new file uploaded, retain existing image_url
                elif image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    full_image_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                    try:
                        image_file.save(full_image_path)
                        new_image_url_for_db = os.path.join('uploads', 'recipes', unique_filename).replace('\\','/')

                        # OPTIONAL: delete the old image file from server if new one is uploaded
                        if recipe[4]:       # Check if old image_url existed
                            old_image_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', recipe[4])
                            if os.path.exists(old_image_full_path):
                                os.remove(old_image_full_path)
                                # print(f"DEBUG: Deleted old image file: {old_image_fulll_path}")   # For debugging
                    except Exception as e:
                        flash(f'Failed to save new image: {e}. Please try ageain.', 'error')
                        return redirect(url_for('recipes.edit_recipe', recipe_id=recipe_id))
                else:
                    flash('Invalid new image file type. Please upload a JPG, PNG, or GIF.', 'error')
                    return redirect(url_for('recipes.edit_recipe', recipe_id=recipe_id))

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE recipes SET recipe_name=%s, prep_time=%s, cook_time=%s, instructions=%s, image_url=%s, description=%s, ingredients=%s WHERE recipe_id=%s AND creator_account_id=%s",
                        (recipe_name, prep_time, cook_time, instructions, new_image_url_for_db, description, ingredients, recipe_id, account_id))
            conn.commit()
            cur.close()
            conn.close()
            flash('Recipe udpated successfully!', 'success')
            return redirect(url_for('recipes.view_my_recipes'))         # Redirect back to view my_recipes
        
        # If GET request, display edit form
        # --- START DEBUG PRINTS FOR GET REQUEST ---
        print(f"\n--- DEBUG: Inside edit_recipe GET path for recipe_id: {recipe_id} ---")
        print(f"Fetched recipe data from DB (single tuple): {recipe}")
        print(f"Type of fetched recipe data: {type(recipe)}")
        if recipe: # Check if recipe tuple exists before accessing indices
            print(f"Recipe Name (recipe[0]): {recipe[0]}")
            print(f"Instructions (recipe[3]): {recipe[3]}")
            print(f"Description (recipe[5]): {recipe[5]}")
            print(f"Ingredients (recipe[6]): {recipe[6]}")
        else: # This 'else' block inside 'if recipe:' should ideally not be hit.
              # It means recipe was True but somehow became None, which is odd.
            print("ERROR: Recipe data is None after initial fetch, check logic.")
        print("------------------------------------------------------------------\n")
        
        # If GET request, display edit form
        return render_template('edit_recipe.html', recipe=recipe, recipe_id=recipe_id)
    else:
        flash('Recipe not found or you do not have permissions to edit it.', 'danger')
        return redirect(url_for('recipes.view_my_recipes'))
    
@recipes_bp.route('/view/<int:recipe_id>', methods=['GET', 'POST'])
def view_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT recipe_name, prep_time, cook_time, instructions, image_url, description, ingredients, creator_account_id, recipe_id FROM recipes WHERE recipe_id=%s", (recipe_id,))
    recipe = cur.fetchone()
    cur.close()
    conn.close()

    if recipe:
         # --- ADD THESE DEBUG PRINT STATEMENTS ---
        print(f"DEBUG: current_user.is_authenticated: {current_user.is_authenticated}")
        if current_user.is_authenticated:
            print(f"DEBUG: current_user.id: {type(current_user.id)} - {current_user.id}")
        else:
            print("DEBUG: current_user is NOT authenticated.")
        print(f"DEBUG: recipe[7] (creator_account_id): {type(recipe[7])} - {recipe[7]}")

        return render_template('view_recipe.html', recipe=recipe, recipe_id=recipe_id)
    else:
        flash('Recipe not found.', 'warning')
        return redirect(url_for('index'))
    
@recipes_bp.route('/delete/<int:recipe_id>', methods=['POST'])
@login_required 
def delete_recipe(recipe_id):
    account_id = current_user.id 
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch image_url here if you want to delete the file from disk too
    cur.execute("SELECT image_url FROM recipes WHERE recipe_id = %s AND creator_account_id = %s", (recipe_id, account_id))
    image_to_delete = cur.fetchone() # This will be (image_url_string,) or None

    if image_to_delete: # If recipe found and belongs to user
        # OPTIONAL: Delete the image file from the server's disk
        if image_to_delete[0]: # Check if there was an actual image_url string
            # Construct the full path to the image file
            full_image_path_to_delete = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', image_to_delete[0])
            if os.path.exists(full_image_path_to_delete):
                try:
                    os.remove(full_image_path_to_delete) # Delete the file
                    # print(f"DEBUG: Deleted image file: {full_image_path_to_delete}") # For debugging
                except Exception as e:
                    print(f"ERROR: Could not delete image file {full_image_path_to_delete}: {e}")
                    # You might flash an error here if deleting the file is critical
        
        # Now delete the record from the database
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
