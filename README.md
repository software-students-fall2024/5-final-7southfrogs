[![Web App CI/CD Pipeline](https://github.com/software-students-fall2024/5-final-7southfrogs/actions/workflows/web-app.yml/badge.svg)](https://github.com/software-students-fall2024/5-final-7southfrogs/actions/workflows/web-app.yml)

# Final Project- What's Cookin 🍳✨

## Project Description
What's Cookin' is a user-friendly web application designed to simplify meal planning and recipe discovery. Users can create an account, manage their pantry, set dietary preferences, and search for recipes tailored to their needs. With features like saving favorite recipes, marking meals as "made," and detailed nutritional information, What's Cookin' makes cooking accessible, personalized, and fun. Perfect for home cooks looking to maximize what they have and minimize waste!

## DockerHub Container Images
[Link to DockerHub](https://hub.docker.com/repositories/dave147)

## Team Members
- [Alex Ruan](https://github.com/axruan)
- [Angela Zhang](https://github.com/angelazzh)
- [Leo Bernarbezheng](https://github.com/leonaurdo)
- [David Lai](https://github.com/danonymouse)

## How to Run the Project

### **Prerequisites**
1. **Python:** Ensure you have Python 3.10 or higher installed.
2. **Docker:** Install the Docker desktop app to run the MongoDB and web app servics.
3. **Environment Variables:** Prepare a .env file for both the database and web app.

### **Clone the Repository**
```bash
    git clone https://github.com/software-students-fall2024/5-final-7southfrogs.git
```
### **Change Directory**
```bash
    cd 5-final-7southfrogs
```

### **Set Up Environment Variables**
- Create a .env file in the root directory of the repository.
- Please check Discord for more information about the .env file.


### **Install Dependencies**
- Install the required dependencies by running the following command:
```bash
    pip install -r requirements.txt
```

### **Building the Containers with Docker**
- Open the Docker application and register for an account (if you don't have one already).
- Keep the application running in the background and start/buiild Docker by:
    ```bash
        docker compose up --force-recreate --build
    ```
- Wait for the containers to build and start.
- Open your browser and navigate to http://localhost:5000 to access the web app.

### **Navigating What's Cookin'**
- Register an account and log in.
- Navigate to the "Profile" page to set your dietary preferences.
- Navigate to the "Pantry" page and add ingredients in your pantry.
- Navigate to the "Home" page to find recipes based on your pantry ingredients anddietary preferences.
- A list of recipes will pop up and you are able to browse through them and save them to your "Saved Recipes" page.
- You can also view your saved recipes on the "Saved Recipes" page and mark as "I made it". 

### **Shut Down the Docker Containers**
- To shut down the Docker containers, run:
    ```bash
        docker compose down
    ```