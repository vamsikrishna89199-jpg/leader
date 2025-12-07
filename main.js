// Main Application Script

// Global State
let currentUser = null;

// DOM Elements
const getStartedBtn = document.getElementById('getStartedBtn');
const learnMoreBtn = document.getElementById('learnMoreBtn');
const scanArea = document.getElementById('scanArea');
const foodImageInput = document.getElementById('foodImageInput');
const scanBtn = document.getElementById('scanBtn');
const mealForm = document.getElementById('mealForm');
const foodSearch = document.getElementById('foodSearch');
const searchFoodBtn = document.getElementById('searchFoodBtn');
const workoutForm = document.getElementById('workoutForm');
const generateMealPlanBtn = document.getElementById('generateMealPlanBtn');
const generateMealPlanCard = document.getElementById('generateMealPlanCard');
const viewGroceryBtn = document.getElementById('viewGroceryBtn');
const viewGroceryCard = document.getElementById('viewGroceryCard');
const groceryListSection = document.getElementById('groceryListSection');
const postBtn = document.getElementById('postBtn');
const friendSearch = document.getElementById('friendSearch');
const searchUserBtn = document.getElementById('searchUserBtn');
const authModal = document.getElementById('authModal');
const loginBtn = document.getElementById('loginBtn');
const addFirstItemBtn = document.getElementById('addFirstItemBtn');
const printGroceryBtn = document.getElementById('printGroceryBtn');
const shareGroceryBtn = document.getElementById('shareGroceryBtn');

// Suggested Users Data
const suggestedUsers = [
    { id: 1, username: 'FitnessFreak', avatar: 'FF', bio: 'Marathon runner & nutrition enthusiast', meal_count: 245, workout_count: 156, level: 5, mutual_friends: 3 },
    { id: 2, username: 'HealthyHabits', avatar: 'HH', bio: 'Plant-based lifestyle advocate', meal_count: 189, workout_count: 92, level: 4, mutual_friends: 2 },
    { id: 3, username: 'GymGuru', avatar: 'GG', bio: 'Strength training specialist', meal_count: 312, workout_count: 278, level: 7, mutual_friends: 5 },
    { id: 4, username: 'YogaMaster', avatar: 'YM', bio: 'Mindfulness & flexibility coach', meal_count: 167, workout_count: 201, level: 6, mutual_friends: 1 },
    { id: 5, username: 'MealPrepPro', avatar: 'MP', bio: 'Weekly meal prep expert', meal_count: 421, workout_count: 89, level: 8, mutual_friends: 4 },
    { id: 6, username: 'WellnessWarrior', avatar: 'WW', bio: 'Holistic health practitioner', meal_count: 276, workout_count: 134, level: 5, mutual_friends: 2 }
];

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeTabs();
    checkAuthStatus();
    loadSuggestedFriends();
});

function initializeEventListeners() {
    // Hero buttons
    if (getStartedBtn) {
        getStartedBtn.onclick = () => showAuthModal();
    }
    if (learnMoreBtn) {
        learnMoreBtn.onclick = () => {
            document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });
        };
    }

    // Food scanning
    if (scanArea) {
        scanArea.onclick = () => foodImageInput.click();
    }
    if (foodImageInput) {
        foodImageInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                previewImage(file);
                scanBtn.disabled = false;
            }
        };
    }
    if (scanBtn) {
        scanBtn.onclick = scanFood;
    }

    // Meal form
    if (mealForm) {
        mealForm.onsubmit = addMeal;
    }

    // Food search
    if (searchFoodBtn) {
        searchFoodBtn.onclick = searchFoods;
    }
    if (foodSearch) {
        foodSearch.onkeypress = (e) => {
            if (e.key === 'Enter') searchFoods();
        };
    }

    // Workout form
    if (workoutForm) {
        workoutForm.onsubmit = addWorkout;
    }

    // Planning actions
    if (generateMealPlanBtn) {
        generateMealPlanBtn.onclick = generateMealPlan;
    }
    if (generateMealPlanCard) {
        generateMealPlanCard.onclick = generateMealPlan;
    }
    if (viewGroceryBtn) {
        viewGroceryBtn.onclick = toggleGroceryList;
    }
    if (viewGroceryCard) {
        viewGroceryCard.onclick = toggleGroceryList;
    }
    if (addFirstItemBtn) {
        addFirstItemBtn.onclick = addGroceryItem;
    }
    if (printGroceryBtn) {
        printGroceryBtn.onclick = printGroceryList;
    }
    if (shareGroceryBtn) {
        shareGroceryBtn.onclick = shareGroceryList;
    }

    // Social features
    if (postBtn) {
        postBtn.onclick = createPost;
    }
    if (searchUserBtn) {
        searchUserBtn.onclick = searchUsers;
    }
    if (friendSearch) {
        friendSearch.onkeypress = (e) => {
            if (e.key === 'Enter') searchUsers();
        };
    }

    // Auth modal
    if (loginBtn) {
        loginBtn.onclick = () => showAuthModal();
    }

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');
    if (menuToggle && navMenu) {
        menuToggle.onclick = () => {
            navMenu.classList.toggle('active');
        };
    }

    // Close modal when clicking outside
    if (authModal) {
        authModal.onclick = (e) => {
            if (e.target === authModal) {
                hideAuthModal();
            }
        };
    }

    // Smooth scrolling for nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
                
                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(l => {
                    l.classList.remove('active');
                });
                link.classList.add('active');
                
                // Close mobile menu
                if (navMenu) {
                    navMenu.classList.remove('active');
                }
            }
        };
    });

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.onclick = () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        };
    });

    // Auth tab switching
    document.querySelectorAll('.auth-tab').forEach(btn => {
        btn.onclick = () => {
            const tabId = btn.getAttribute('data-tab');
            switchAuthTab(tabId);
        };
    });

    // Close modal buttons
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.onclick = () => {
            hideAuthModal();
        };
    });
}

function initializeTabs() {
    // Set first tab as active by default
    const firstTab = document.querySelector('.tab-btn');
    if (firstTab) {
        switchTab(firstTab.getAttribute('data-tab'));
    }

    // Set first auth tab as active
    const firstAuthTab = document.querySelector('.auth-tab');
    if (firstAuthTab) {
        switchAuthTab(firstAuthTab.getAttribute('data-tab'));
    }
}

function switchTab(tabId) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === tabId) {
            content.classList.add('active');
        }
    });

    // Load tab-specific data
    switch (tabId) {
        case 'food-scan':
            // Already initialized
            break;
        case 'meal-log':
            loadRecentMeals();
            break;
        case 'nutrition-db':
            loadFoodDatabase();
            break;
        case 'social-feed':
            loadSocialFeed();
            break;
        case 'social-friends':
            loadFriendsList();
            break;
        case 'social-search':
            // Already initialized
            break;
    }
}

function switchAuthTab(tabId) {
    // Update auth tab buttons
    document.querySelectorAll('.auth-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });

    // Update auth form content
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
        if (form.id === `${tabId}Form`) {
            form.classList.add('active');
        }
    });
}

function showAuthModal() {
    if (authModal) {
        authModal.classList.add('active');
    }
}

function hideAuthModal() {
    if (authModal) {
        authModal.classList.remove('active');
    }
}

function checkAuthStatus() {
    // Check if user is authenticated
    if (auth && auth.isAuthenticated) {
        currentUser = auth.currentUser;
        loadDashboard();
        loadRecentMeals();
        loadWorkoutHistory();
        loadSocialFeed();
        loadFriendsList();
    } else {
        // Show auth modal after delay
        setTimeout(() => {
            if (!auth || !auth.isAuthenticated) {
                showAuthModal();
            }
        }, 1000);
    }
}

// Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <div class="toast-content">
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Dashboard Functions
async function loadDashboard() {
    try {
        // Mock data for demo
        const mockStats = {
            nutrition: { calories: 1250, protein: 85, carbs: 120, fat: 45 },
            goals: { calories: 2000, protein: 150, water: 2500 },
            water: 1500,
            workouts: { count: 3, calories: 420 },
            fasting: { active: false }
        };
        renderDashboard(mockStats);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
    }
}

function renderDashboard(stats) {
    const dashboardContent = document.getElementById('dashboardContent');
    if (!dashboardContent) return;

    dashboardContent.innerHTML = `
        <div class="dashboard-card">
            <h3><i class="fas fa-utensils"></i> Today's Nutrition</h3>
            <div class="stat-item">
                <span class="stat-label">Calories</span>
                <span class="stat-value">${stats.nutrition.calories} / ${stats.goals.calories}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Protein</span>
                <span class="stat-value">${stats.nutrition.protein}g / ${stats.goals.protein}g</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Carbs</span>
                <span class="stat-value">${stats.nutrition.carbs}g</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Fat</span>
                <span class="stat-value">${stats.nutrition.fat}g</span>
            </div>
        </div>

        <div class="dashboard-card">
            <h3><i class="fas fa-droplet"></i> Hydration</h3>
            <div class="stat-item">
                <span class="stat-label">Water Intake</span>
                <span class="stat-value">${stats.water}ml / ${stats.goals.water}ml</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min((stats.water / stats.goals.water) * 100, 100)}%"></div>
            </div>
            <button class="btn btn-sm btn-primary" onclick="addWater(250)">Add 250ml</button>
        </div>

        <div class="dashboard-card">
            <h3><i class="fas fa-dumbbell"></i> Workouts</h3>
            <div class="stat-item">
                <span class="stat-label">Today's Workouts</span>
                <span class="stat-value">${stats.workouts.count}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Calories Burned</span>
                <span class="stat-value">${stats.workouts.calories}</span>
            </div>
            <button class="btn btn-sm btn-primary" onclick="switchTab('fitness')">Log Workout</button>
        </div>

        <div class="dashboard-card">
            <h3><i class="fas fa-clock"></i> Fasting</h3>
            ${stats.fasting.active ? `
                <div class="stat-item">
                    <span class="stat-label">Fasting Time</span>
                    <span class="stat-value">${stats.fasting.elapsedHours}h</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(stats.fasting.elapsedHours / 16) * 100}%"></div>
                </div>
                <button class="btn btn-sm btn-danger" onclick="endFasting()">End Fast</button>
            ` : `
                <p>No active fasting session</p>
                <button class="btn btn-sm btn-primary" onclick="startFasting(16)">Start 16h Fast</button>
            `}
        </div>
    `;
}

// Food Scanning Functions
function previewImage(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        scanArea.innerHTML = `
            <img src="${e.target.result}" alt="Food preview" style="max-width: 100%; border-radius: 8px; max-height: 200px;">
            <p>Click to change image</p>
        `;
    };
    reader.readAsDataURL(file);
}

async function scanFood() {
    const file = foodImageInput.files[0];
    if (!file) {
        showToast('Please select an image first', 'warning');
        return;
    }

    try {
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';

        // Mock API call
        setTimeout(() => {
            const mockFood = {
                name: 'Avocado Toast',
                confidence: 0.92,
                calories: 350,
                protein: 12,
                carbs: 35,
                fat: 18
            };

            const resultsDiv = document.getElementById('scanResults');
            resultsDiv.innerHTML = `
                <h3>Scan Results</h3>
                <div class="food-result">
                    <h4>${mockFood.name}</h4>
                    <div class="food-nutrition">
                        <span><i class="fas fa-fire"></i> ${mockFood.calories} kcal</span>
                        <span><i class="fas fa-drumstick-bite"></i> ${mockFood.protein}g protein</span>
                        <span><i class="fas fa-bread-slice"></i> ${mockFood.carbs}g carbs</span>
                        <span><i class="fas fa-oil-can"></i> ${mockFood.fat}g fat</span>
                    </div>
                    <div class="food-confidence">
                        <span class="confidence-badge">${(mockFood.confidence * 100).toFixed(1)}% confidence</span>
                    </div>
                    <button class="btn btn-primary" onclick="addScannedMeal()">
                        <i class="fas fa-plus"></i> Add to Today's Meals
                    </button>
                </div>
            `;
            
            showToast('Food scanned successfully!', 'success');
            scanBtn.disabled = false;
            scanBtn.innerHTML = 'Scan Food';
        }, 1500);
    } catch (error) {
        showToast(error.message || 'Scan failed', 'error');
        scanBtn.disabled = false;
        scanBtn.innerHTML = 'Scan Food';
    }
}

function addScannedMeal() {
    showToast('Meal added successfully!', 'success');
}

// Meal Functions
async function addMeal(e) {
    e.preventDefault();

    const mealData = {
        name: document.getElementById('mealName').value,
        meal_type: document.getElementById('mealType').value,
        calories: parseFloat(document.getElementById('calories').value),
        protein: parseFloat(document.getElementById('protein').value),
        carbs: parseFloat(document.getElementById('carbs').value),
        fat: parseFloat(document.getElementById('fat').value)
    };

    try {
        // Mock API call
        showToast('Meal logged successfully!', 'success');
        mealForm.reset();
        loadRecentMeals();
    } catch (error) {
        showToast(error.message || 'Failed to log meal', 'error');
    }
}

async function loadRecentMeals() {
    try {
        // Mock data
        const mockMeals = [
            { id: 1, name: 'Avocado Toast', meal_type: 'breakfast', calories: 350, protein: 12, carbs: 35, fat: 18, date: new Date() },
            { id: 2, name: 'Grilled Chicken Salad', meal_type: 'lunch', calories: 420, protein: 35, carbs: 20, fat: 22, date: new Date(Date.now() - 3600000) },
            { id: 3, name: 'Protein Smoothie', meal_type: 'snack', calories: 320, protein: 25, carbs: 40, fat: 8, date: new Date(Date.now() - 7200000) }
        ];
        renderRecentMeals(mockMeals);
    } catch (error) {
        console.error('Failed to load meals:', error);
    }
}

function renderRecentMeals(meals) {
    const container = document.getElementById('recentMeals');
    if (!container) return;

    if (meals.length === 0) {
        container.innerHTML = '<p class="no-data">No meals logged today</p>';
        return;
    }

    container.innerHTML = `
        <h3>Recent Meals</h3>
        <div class="meals-list">
            ${meals.map(meal => `
                <div class="meal-item">
                    <div class="meal-item-header">
                        <h5>${meal.name}</h5>
                        <span class="meal-type">${meal.meal_type}</span>
                    </div>
                    <div class="meal-nutrition">
                        <span><i class="fas fa-fire"></i> ${meal.calories} kcal</span>
                        <span><i class="fas fa-drumstick-bite"></i> ${meal.protein}g</span>
                        <span><i class="fas fa-bread-slice"></i> ${meal.carbs}g</span>
                        <span><i class="fas fa-oil-can"></i> ${meal.fat}g</span>
                    </div>
                    <div class="meal-time">${new Date(meal.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
            `).join('')}
        </div>
    `;
}

// Food Database Functions
async function loadFoodDatabase() {
    try {
        // Mock data
        const mockFoods = [
            { id: 1, name: 'Chicken Breast', category: 'Protein', calories: 165, protein: 31, carbs: 0, fat: 3.6, serving_size: '100g' },
            { id: 2, name: 'Brown Rice', category: 'Grains', calories: 112, protein: 2.6, carbs: 23, fat: 0.9, serving_size: '100g cooked' },
            { id: 3, name: 'Avocado', category: 'Fruit', calories: 160, protein: 2, carbs: 9, fat: 15, serving_size: '100g' },
            { id: 4, name: 'Greek Yogurt', category: 'Dairy', calories: 59, protein: 10, carbs: 3.6, fat: 0.4, serving_size: '100g' },
            { id: 5, name: 'Broccoli', category: 'Vegetables', calories: 34, protein: 2.8, carbs: 7, fat: 0.4, serving_size: '100g' }
        ];
        renderFoodDatabase(mockFoods);
    } catch (error) {
        console.error('Failed to load food database:', error);
    }
}

async function searchFoods() {
    const query = foodSearch.value.trim();
    if (!query) {
        showToast('Please enter a search term', 'warning');
        return;
    }

    try {
        // Mock search
        showToast(`Searching for "${query}"...`, 'info');
        // In real app, make API call
    } catch (error) {
        showToast(error.message || 'Search failed', 'error');
    }
}

function renderFoodDatabase(foods) {
    const container = document.getElementById('foodDatabase');
    if (!container) return;

    if (foods.length === 0) {
        container.innerHTML = '<p class="no-data">No foods found</p>';
        return;
    }

    container.innerHTML = foods.map(food => `
        <div class="food-item">
            <div class="food-info">
                <h4>${food.name}</h4>
                <div class="food-details">
                    <span class="food-category">${food.category}</span>
                    <span class="serving-size">${food.serving_size}</span>
                </div>
            </div>
            <div class="food-nutrition">
                <span><i class="fas fa-fire"></i> ${food.calories}</span>
                <span><i class="fas fa-drumstick-bite"></i> ${food.protein}g</span>
                <span><i class="fas fa-bread-slice"></i> ${food.carbs}g</span>
                <span><i class="fas fa-oil-can"></i> ${food.fat}g</span>
            </div>
        </div>
    `).join('');
}

// Workout Functions
async function addWorkout(e) {
    e.preventDefault();

    const workoutData = {
        name: document.getElementById('workoutName').value,
        workout_type: document.getElementById('workoutType').value,
        duration: parseInt(document.getElementById('duration').value),
        calories_burned: parseInt(document.getElementById('caloriesBurned').value),
        intensity: 'medium'
    };

    try {
        showToast('Workout logged successfully!', 'success');
        workoutForm.reset();
        loadWorkoutHistory();
    } catch (error) {
        showToast(error.message || 'Failed to log workout', 'error');
    }
}

async function loadWorkoutHistory() {
    try {
        // Mock data
        const mockWorkouts = [
            { id: 1, name: 'Morning Run', workout_type: 'cardio', duration: 30, calories_burned: 320, date: new Date() },
            { id: 2, name: 'Strength Training', workout_type: 'strength', duration: 45, calories_burned: 280, date: new Date(Date.now() - 86400000) },
            { id: 3, name: 'Yoga Session', workout_type: 'flexibility', duration: 60, calories_burned: 180, date: new Date(Date.now() - 172800000) }
        ];
        renderWorkoutHistory(mockWorkouts);
    } catch (error) {
        console.error('Failed to load workouts:', error);
    }
}

function renderWorkoutHistory(workouts) {
    const container = document.getElementById('workoutHistory');
    if (!container) return;

    if (workouts.length === 0) {
        container.innerHTML = '<p class="no-data">No workouts logged recently</p>';
        return;
    }

    container.innerHTML = workouts.map(workout => `
        <div class="workout-item">
            <div class="workout-header">
                <h5>${workout.name}</h5>
                <span class="workout-type">${workout.workout_type}</span>
            </div>
            <div class="workout-details">
                <span><i class="fas fa-clock"></i> ${workout.duration} min</span>
                <span><i class="fas fa-fire"></i> ${workout.calories_burned} kcal</span>
            </div>
            <div class="workout-time">${new Date(workout.date).toLocaleDateString()}</div>
        </div>
    `).join('');
}

// Planning Functions
async function generateMealPlan() {
    try {
        // Show loading state
        const originalText = generateMealPlanBtn.innerHTML;
        generateMealPlanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        generateMealPlanBtn.disabled = true;

        // Mock API call
        setTimeout(() => {
            const mockPlan = getMockMealPlan();
            renderMealPlan(mockPlan);
            
            showToast('Weekly meal plan generated successfully!', 'success');
            
            // Reset button state
            generateMealPlanBtn.innerHTML = originalText;
            generateMealPlanBtn.disabled = false;
            
            // Suggest grocery list but DON'T automatically show it
            suggestGroceryList();
            
        }, 1500);
    } catch (error) {
        showToast(error.message || 'Failed to generate meal plan', 'error');
        generateMealPlanBtn.innerHTML = 'Generate Now';
        generateMealPlanBtn.disabled = false;
    }
}

function getMockMealPlan() {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const mealTypes = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];
    const mockMeals = [
        { name: 'Avocado Toast', calories: 350, protein: 12, carbs: 35, fat: 18 },
        { name: 'Greek Yogurt Bowl', calories: 280, protein: 20, carbs: 25, fat: 10 },
        { name: 'Chicken Salad', calories: 420, protein: 35, carbs: 20, fat: 22 },
        { name: 'Salmon Quinoa', calories: 520, protein: 40, carbs: 45, fat: 25 },
        { name: 'Protein Smoothie', calories: 320, protein: 25, carbs: 40, fat: 8 },
        { name: 'Vegetable Stir Fry', calories: 380, protein: 15, carbs: 45, fat: 18 },
        { name: 'Turkey Wrap', calories: 410, protein: 28, carbs: 38, fat: 16 }
    ];

    const plan = {};
    const today = new Date();
    
    days.forEach((day, index) => {
        const date = new Date(today);
        date.setDate(date.getDate() + index);
        
        plan[day] = mealTypes.map(type => {
            const meal = mockMeals[Math.floor(Math.random() * mockMeals.length)];
            return {
                name: meal.name,
                meal_type: type.toLowerCase(),
                calories: meal.calories + Math.floor(Math.random() * 50 - 25),
                protein: meal.protein + Math.floor(Math.random() * 5 - 2),
                carbs: meal.carbs + Math.floor(Math.random() * 10 - 5),
                fat: meal.fat + Math.floor(Math.random() * 3 - 1)
            };
        });
    });

    return plan;
}

function renderMealPlan(plans) {
    const container = document.getElementById('mealPlanCalendar');
    if (!container) return;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const today = new Date();

    container.innerHTML = days.map(day => {
        const date = new Date(today);
        const dayIndex = days.indexOf(day);
        date.setDate(today.getDate() + dayIndex);

        return `
            <div class="day-plan">
                <div class="day-header">
                    <span>${day}</span>
                    <span class="day-date">${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                </div>
                ${plans[day] ? plans[day].map(meal => `
                    <div class="meal-item">
                        <div class="meal-item-header">
                            <h5>${meal.name}</h5>
                            <span class="meal-type">${meal.meal_type}</span>
                        </div>
                        <div class="meal-nutrition">
                            <span><i class="fas fa-fire"></i> ${meal.calories} kcal</span>
                            <span><i class="fas fa-drumstick-bite"></i> ${meal.protein}g</span>
                            <span><i class="fas fa-bread-slice"></i> ${meal.carbs}g</span>
                            <span><i class="fas fa-oil-can"></i> ${meal.fat}g</span>
                        </div>
                    </div>
                `).join('') : '<p class="no-data">No meals planned</p>'}
            </div>
        `;
    }).join('');
}

function toggleGroceryList() {
    const groceryListSection = document.getElementById('groceryListSection');
    const viewGroceryBtn = document.getElementById('viewGroceryBtn');
    
    if (groceryListSection.classList.contains('active')) {
        // Hide the list
        groceryListSection.classList.remove('active');
        if (viewGroceryBtn) {
            viewGroceryBtn.textContent = 'View List';
        }
    } else {
        // Show the list
        groceryListSection.classList.add('active');
        if (viewGroceryBtn) {
            viewGroceryBtn.textContent = 'Hide List';
        }
        // Scroll to grocery list
        setTimeout(() => {
            groceryListSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
}

function suggestGroceryList() {
    const mockItems = {
        'Produce': [
            { id: 1, name: 'Avocados', quantity: '3 pieces', purchased: false },
            { id: 2, name: 'Spinach', quantity: '1 bag', purchased: false },
            { id: 3, name: 'Bell Peppers', quantity: '2 pieces', purchased: false },
            { id: 4, name: 'Broccoli', quantity: '1 head', purchased: false }
        ],
        'Protein': [
            { id: 5, name: 'Chicken Breast', quantity: '500g', purchased: false },
            { id: 6, name: 'Salmon Fillet', quantity: '2 pieces', purchased: false },
            { id: 7, name: 'Greek Yogurt', quantity: '2 containers', purchased: true }
        ],
        'Pantry': [
            { id: 8, name: 'Quinoa', quantity: '1 bag', purchased: false },
            { id: 9, name: 'Olive Oil', quantity: '1 bottle', purchased: true },
            { id: 10, name: 'Oats', quantity: '1 package', purchased: false }
        ]
    };

    renderGroceryList(mockItems);
    showToast('Grocery list suggested based on your meal plan!', 'info');
}

function renderGroceryList(items) {
    const container = document.getElementById('groceryList');
    if (!container) return;

    if (!items || Object.keys(items).length === 0) {
        container.innerHTML = `
            <div class="no-data-message">
                <i class="fas fa-shopping-cart"></i>
                <h4>Your grocery list is empty</h4>
                <p>Generate a meal plan to automatically create a grocery list, or add items manually.</p>
                <button class="btn btn-primary" id="addFirstItemBtn">
                    <i class="fas fa-plus"></i> Add First Item
                </button>
            </div>
        `;
        
        // Re-attach event listener
        const addFirstItemBtn = document.getElementById('addFirstItemBtn');
        if (addFirstItemBtn) {
            addFirstItemBtn.onclick = addGroceryItem;
        }
        updateGroceryStats();
        return;
    }

    let totalItems = 0;
    let purchasedCount = 0;

    container.innerHTML = Object.entries(items).map(([category, categoryItems]) => {
        const categoryPurchased = categoryItems.filter(item => item.purchased).length;
        purchasedCount += categoryPurchased;
        totalItems += categoryItems.length;
        const icon = getCategoryIcon(category);

        return `
            <div class="grocery-category">
                <div class="grocery-category-header">
                    <div class="category-icon">${icon}</div>
                    <h4>${category}</h4>
                    <span class="category-count">${categoryPurchased}/${categoryItems.length}</span>
                </div>
                <div class="grocery-items">
                    ${categoryItems.map(item => `
                        <div class="grocery-item ${item.purchased ? 'purchased' : ''}" onclick="toggleGroceryItem(${item.id})">
                            <div class="grocery-check">
                                <i class="fas fa-${item.purchased ? 'check' : ''}"></i>
                            </div>
                            <div class="grocery-name">${item.name}</div>
                            <div class="grocery-quantity">${item.quantity}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');

    updateGroceryStats(totalItems, purchasedCount);
}

function getCategoryIcon(category) {
    const icons = {
        'Produce': '🥬',
        'Protein': '🍗',
        'Pantry': '🥫',
        'Dairy': '🥛',
        'Bakery': '🍞',
        'Frozen': '❄️',
        'Beverages': '🥤'
    };
    return icons[category] || '🛒';
}

function updateGroceryStats(total = 0, purchased = 0) {
    const totalEl = document.getElementById('totalItems');
    const purchasedEl = document.getElementById('purchasedCount');
    const pendingEl = document.getElementById('pendingCount');

    if (totalEl) totalEl.textContent = total;
    if (purchasedEl) purchasedEl.textContent = purchased;
    if (pendingEl) pendingEl.textContent = total - purchased;
}

function addGroceryItem() {
    const itemName = prompt('Enter item name:');
    if (itemName) {
        const quantity = prompt('Enter quantity (optional):', '1 item');
        showToast(`${itemName} added to grocery list!`, 'success');
        // In real app, add to list and re-render
    }
}

function toggleGroceryItem(itemId) {
    showToast('Item toggled!', 'info');
    // In real app, update item status and re-render
}

function printGroceryList() {
    showToast('Printing grocery list...', 'info');
    // In real app, implement print functionality
}

function shareGroceryList() {
    showToast('Sharing grocery list...', 'info');
    // In real app, implement share functionality
}

// Social Functions
async function createPost() {
    const content = document.getElementById('postContent').value.trim();
    if (!content) {
        showToast('Please enter some content', 'warning');
        return;
    }

    try {
        showToast('Post created successfully!', 'success');
        document.getElementById('postContent').value = '';
        loadSocialFeed();
    } catch (error) {
        showToast(error.message || 'Failed to create post', 'error');
    }
}

async function loadSocialFeed() {
    try {
        // Mock data
        const mockPosts = [
            {
                id: 1,
                user: { username: 'FitnessFreak', avatar: 'FF' },
                content: 'Just completed my first marathon! So proud of this accomplishment. Consistency and proper nutrition made all the difference!',
                created_at: new Date(Date.now() - 3600000),
                likes_count: 42,
                comments_count: 8,
                liked: false
            },
            {
                id: 2,
                user: { username: 'HealthyHabits', avatar: 'HH' },
                content: 'Meal prep Sunday complete! All set for a healthy week ahead. Pro tip: Batch cooking saves so much time during busy weeks.',
                created_at: new Date(Date.now() - 7200000),
                likes_count: 28,
                comments_count: 5,
                liked: true
            },
            {
                id: 3,
                user: { username: 'GymGuru', avatar: 'GG' },
                content: 'New personal record on deadlifts today! 225lbs 💪 Remember, progressive overload is key to strength gains.',
                created_at: new Date(Date.now() - 86400000),
                likes_count: 56,
                comments_count: 12,
                liked: false
            }
        ];
        renderSocialFeed(mockPosts);
    } catch (error) {
        console.error('Failed to load social feed:', error);
    }
}

function renderSocialFeed(posts) {
    const container = document.getElementById('socialFeed');
    if (!container) return;

    if (posts.length === 0) {
        container.innerHTML = '<p class="no-data">No posts yet. Be the first to post!</p>';
        return;
    }

    container.innerHTML = posts.map(post => `
        <div class="post">
            <div class="post-header">
                <div class="post-avatar">${post.user.avatar}</div>
                <div class="post-user">
                    <h4>${post.user.username}</h4>
                    <div class="post-time">${new Date(post.created_at).toLocaleString()}</div>
                </div>
            </div>
            <div class="post-content">${post.content}</div>
            <div class="post-actions">
                <button class="post-action ${post.liked ? 'liked' : ''}" onclick="likePost(${post.id})">
                    <i class="fas fa-heart"></i> ${post.likes_count}
                </button>
                <button class="post-action" onclick="showComments(${post.id})">
                    <i class="fas fa-comment"></i> ${post.comments_count}
                </button>
                <button class="post-action" onclick="sharePost(${post.id})">
                    <i class="fas fa-share"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function likePost(postId) {
    showToast('Post liked!', 'info');
    // In real app, make API call and refresh feed
}

function showComments(postId) {
    showToast('Comments feature coming soon!', 'info');
}

function sharePost(postId) {
    showToast('Share feature coming soon!', 'info');
}

async function loadFriendsList() {
    try {
        // Mock data - no friends for new users
        const mockFriends = [];
        renderFriendsList(mockFriends);
    } catch (error) {
        console.error('Failed to load friends list:', error);
    }
}

function renderFriendsList(friends) {
    const container = document.getElementById('friendsList');
    const noFriendsMessage = document.getElementById('noFriendsMessage');
    const friendsCount = document.getElementById('friendsCount');

    if (!friends || friends.length === 0) {
        if (container) container.innerHTML = '';
        if (noFriendsMessage) noFriendsMessage.style.display = 'block';
        if (friendsCount) friendsCount.textContent = '0 friends';
        return;
    }

    if (noFriendsMessage) noFriendsMessage.style.display = 'none';
    if (friendsCount) friendsCount.textContent = `${friends.length} ${friends.length === 1 ? 'friend' : 'friends'}`;

    container.innerHTML = friends.map(friend => `
        <div class="friend-item">
            <div class="friend-avatar">${friend.avatar || friend.username.charAt(0).toUpperCase()}</div>
            <div class="friend-info">
                <h4>${friend.username}</h4>
                ${friend.bio ? `<p class="friend-bio">${friend.bio}</p>` : ''}
                <div class="friend-stats">
                    <span><i class="fas fa-apple-alt"></i> ${friend.meal_count || 0} meals</span>
                    <span><i class="fas fa-dumbbell"></i> ${friend.workout_count || 0} workouts</span>
                </div>
            </div>
            <div class="friend-actions">
                <button class="btn btn-sm btn-primary" onclick="messageFriend(${friend.id})">
                    <i class="fas fa-comment"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="removeFriend(${friend.id})">
                    <i class="fas fa-user-minus"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function loadSuggestedFriends() {
    const container = document.getElementById('suggestedFriends');
    if (!container) return;

    container.innerHTML = suggestedUsers.map(user => `
        <div class="suggested-user">
            <div class="suggested-user-avatar">${user.avatar}</div>
            <h5>${user.username}</h5>
            <p>${user.bio}</p>
            <div class="suggested-user-stats">
                <span><i class="fas fa-apple-alt"></i> ${user.meal_count}</span>
                <span><i class="fas fa-dumbbell"></i> ${user.workout_count}</span>
                ${user.mutual_friends > 0 ? `<span><i class="fas fa-users"></i> ${user.mutual_friends} mutual</span>` : ''}
            </div>
            <button class="btn btn-primary btn-sm" onclick="sendFriendRequest('${user.username}')">
                <i class="fas fa-user-plus"></i> Add Friend
            </button>
        </div>
    `).join('');
}

async function searchUsers() {
    const query = friendSearch.value.trim();
    if (!query) {
        showToast('Please enter a search term', 'warning');
        return;
    }

    try {
        // Mock search results
        const mockResults = suggestedUsers.filter(user => 
            user.username.toLowerCase().includes(query.toLowerCase()) ||
            user.bio.toLowerCase().includes(query.toLowerCase())
        );
        
        renderSearchResults(mockResults);
        
        if (mockResults.length === 0) {
            showToast(`No users found for "${query}"`, 'info');
        }
    } catch (error) {
        showToast(error.message || 'Search failed', 'error');
    }
}

function renderSearchResults(users) {
    const container = document.getElementById('searchResults');
    if (!container) return;

    if (users.length === 0) {
        container.innerHTML = '<p class="no-data">No users found. Try a different search term.</p>';
        return;
    }

    container.innerHTML = users.map(user => `
        <div class="user-item">
            <div class="user-avatar">${user.avatar}</div>
            <div class="user-info">
                <h4>${user.username}</h4>
                <p class="user-bio">${user.bio}</p>
                <div class="user-stats">
                    <span><i class="fas fa-apple-alt"></i> ${user.meal_count}</span>
                    <span><i class="fas fa-dumbbell"></i> ${user.workout_count}</span>
                    <span><i class="fas fa-trophy"></i> Level ${user.level}</span>
                </div>
            </div>
            <div class="user-actions">
                <button class="btn btn-sm btn-primary" onclick="sendFriendRequest('${user.username}')">
                    <i class="fas fa-user-plus"></i> Add
                </button>
            </div>
        </div>
    `).join('');
}

function sendFriendRequest(username) {
    showToast(`Friend request sent to ${username}!`, 'success');
}

function messageFriend(userId) {
    showToast('Messaging feature coming soon!', 'info');
}

function removeFriend(friendId) {
    if (confirm('Are you sure you want to remove this friend?')) {
        showToast('Friend removed', 'success');
    }
}

// Export functions to global scope
window.addWater = (amount) => {
    showToast(`Added ${amount}ml of water`, 'success');
};

window.startFasting = (duration) => {
    showToast(`Started ${duration}-hour fast`, 'success');
    loadDashboard();
};

window.endFasting = () => {
    showToast('Fast completed successfully!', 'success');
    loadDashboard();
};

window.switchTab = switchTab;
window.likePost = likePost;
window.showComments = showComments;
window.sendFriendRequest = sendFriendRequest;
window.messageFriend = messageFriend;
window.removeFriend = removeFriend;
window.addScannedMeal = addScannedMeal;
window.toggleGroceryItem = toggleGroceryItem;
