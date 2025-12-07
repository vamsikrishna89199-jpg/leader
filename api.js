// API Configuration
const API_BASE_URL = window.location.origin;

// API Service Class
class ApiService {
    constructor() {
        this.token = localStorage.getItem('auth_token');
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            ...options,
            headers,
            credentials: 'include'
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    // Auth Endpoints
    async register(username, email, password) {
        return this.request('/api/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
    }

    async login(email, password) {
        return this.request('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async logout() {
        return this.request('/api/logout', {
            method: 'POST'
        });
    }

    async getProfile() {
        return this.request('/api/user/profile');
    }

    async updateProfile(data) {
        return this.request('/api/user/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async uploadProfilePicture(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/api/user/upload-profile-picture', {
            method: 'POST',
            headers: {},
            body: formData
        });
    }

    // Meal Endpoints
    async getMeals(date = null, type = null) {
        let url = '/api/meals';
        const params = new URLSearchParams();
        
        if (date) params.append('date', date);
        if (type) params.append('type', type);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        return this.request(url);
    }

    async addMeal(mealData) {
        return this.request('/api/meals', {
            method: 'POST',
            body: JSON.stringify(mealData)
        });
    }

    async updateMeal(mealId, mealData) {
        return this.request(`/api/meals/${mealId}`, {
            method: 'PUT',
            body: JSON.stringify(mealData)
        });
    }

    async deleteMeal(mealId) {
        return this.request(`/api/meals/${mealId}`, {
            method: 'DELETE'
        });
    }

    async scanFood(imageFile) {
        const formData = new FormData();
        formData.append('image', imageFile);

        return this.request('/api/meals/scan', {
            method: 'POST',
            headers: {},
            body: formData
        });
    }

    // Nutrition Database
    async searchFoods(search, category = '', limit = 50) {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);
        params.append('limit', limit);

        return this.request(`/api/nutrition/database?${params.toString()}`);
    }

    // Diet Calculator
    async calculateDiet(data) {
        return this.request('/api/diet/calculate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Workout Endpoints
    async getWorkouts(date = null, type = null) {
        let url = '/api/workouts';
        const params = new URLSearchParams();
        
        if (date) params.append('date', date);
        if (type) params.append('type', type);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        return this.request(url);
    }

    async addWorkout(workoutData) {
        return this.request('/api/workouts', {
            method: 'POST',
            body: JSON.stringify(workoutData)
        });
    }

    async updateWorkout(workoutId, workoutData) {
        return this.request(`/api/workouts/${workoutId}`, {
            method: 'PUT',
            body: JSON.stringify(workoutData)
        });
    }

    async deleteWorkout(workoutId) {
        return this.request(`/api/workouts/${workoutId}`, {
            method: 'DELETE'
        });
    }

    // Hydration Endpoints
    async getHydration(date = null) {
        const url = date ? `/api/hydration?date=${date}` : '/api/hydration';
        return this.request(url);
    }

    async addWater(amount) {
        return this.request('/api/hydration', {
            method: 'POST',
            body: JSON.stringify({ amount })
        });
    }

    // Sleep Endpoints
    async getSleep(limit = 7) {
        return this.request(`/api/sleep?limit=${limit}`);
    }

    async addSleep(duration, quality) {
        return this.request('/api/sleep', {
            method: 'POST',
            body: JSON.stringify({ duration, quality })
        });
    }

    // Fasting Endpoints
    async getFasting() {
        return this.request('/api/fasting');
    }

    async startFasting(targetDuration = 16) {
        return this.request('/api/fasting', {
            method: 'POST',
            body: JSON.stringify({ target_duration: targetDuration })
        });
    }

    async endFasting(sessionId) {
        return this.request('/api/fasting', {
            method: 'PUT',
            body: JSON.stringify({ session_id: sessionId })
        });
    }

    // Grocery List Endpoints
    async getGroceryList(purchased = false) {
        return this.request(`/api/grocery?purchased=${purchased}`);
    }

    async addGroceryItem(name, quantity = '1', category = 'Other') {
        return this.request('/api/grocery', {
            method: 'POST',
            body: JSON.stringify({ name, quantity, category })
        });
    }

    async updateGroceryItem(itemId, data) {
        return this.request('/api/grocery', {
            method: 'PUT',
            body: JSON.stringify({ id: itemId, ...data })
        });
    }

    async deleteGroceryItem(itemId) {
        return this.request(`/api/grocery?id=${itemId}`, {
            method: 'DELETE'
        });
    }

    // Meal Planning Endpoints
    async getMealPlans(weekStart = null) {
        let url = '/api/meal-plans';
        if (weekStart) {
            url += `?week_start=${weekStart}`;
        }
        return this.request(url);
    }

    async generateMealPlan(weekStart) {
        return this.request('/api/meal-plans', {
            method: 'POST',
            body: JSON.stringify({ week_start: weekStart })
        });
    }

    // Notification Endpoints
    async getNotifications(unreadOnly = false, limit = 20) {
        return this.request(`/api/notifications?unread_only=${unreadOnly}&limit=${limit}`);
    }

    async markNotificationRead(notificationId) {
        return this.request('/api/notifications', {
            method: 'PUT',
            body: JSON.stringify({ id: notificationId })
        });
    }

    async markAllNotificationsRead() {
        return this.request('/api/notifications', {
            method: 'PUT',
            body: JSON.stringify({ mark_all: true })
        });
    }

    // Social Endpoints
    async getFriends(status = 'accepted') {
        return this.request(`/api/social/friends?status=${status}`);
    }

    async sendFriendRequest(username) {
        return this.request('/api/social/friends', {
            method: 'POST',
            body: JSON.stringify({ username, action: 'send' })
        });
    }

    async acceptFriendRequest(friendshipId) {
        return this.request('/api/social/friends', {
            method: 'POST',
            body: JSON.stringify({ friendship_id: friendshipId, action: 'accept' })
        });
    }

    async rejectFriendRequest(friendshipId) {
        return this.request('/api/social/friends', {
            method: 'POST',
            body: JSON.stringify({ friendship_id: friendshipId, action: 'reject' })
        });
    }

    async removeFriend(friendshipId) {
        return this.request(`/api/social/friends?id=${friendshipId}`, {
            method: 'DELETE'
        });
    }

    async getPosts(userId = null, limit = 20, offset = 0) {
        let url = '/api/social/posts';
        const params = new URLSearchParams();
        
        if (userId) params.append('user_id', userId);
        params.append('limit', limit);
        params.append('offset', offset);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        return this.request(url);
    }

    async createPost(content, imageUrl = null) {
        return this.request('/api/social/posts', {
            method: 'POST',
            body: JSON.stringify({ content, image_url: imageUrl })
        });
    }

    async likePost(postId) {
        return this.request(`/api/social/posts/${postId}/like`, {
            method: 'POST'
        });
    }

    async getComments(postId) {
        return this.request(`/api/social/posts/${postId}/comments`);
    }

    async addComment(postId, content) {
        return this.request(`/api/social/posts/${postId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }

    async searchUsers(query, limit = 10) {
        return this.request(`/api/social/search-users?q=${query}&limit=${limit}`);
    }

    // Report Endpoints
    async getWeeklyReport() {
        return this.request('/api/reports/weekly');
    }

    async getMonthlyReport() {
        return this.request('/api/reports/monthly');
    }

    async getReportHistory(type = 'weekly', limit = 10) {
        return this.request(`/api/reports/history?type=${type}&limit=${limit}`);
    }

    // Weight Log Endpoints
    async getWeightLogs(limit = 30) {
        return this.request(`/api/weight-logs?limit=${limit}`);
    }

    async addWeightLog(weight) {
        return this.request('/api/weight-logs', {
            method: 'POST',
            body: JSON.stringify({ weight })
        });
    }

    // Dashboard Stats
    async getDashboardStats() {
        return this.request('/api/dashboard/stats');
    }
}

// Create global API instance
const api = new ApiService();