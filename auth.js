// Authentication Manager
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        // Check for existing session
        const userData = localStorage.getItem('user_data');
        const token = localStorage.getItem('auth_token');
        
        if (userData && token) {
            try {
                this.currentUser = JSON.parse(userData);
                this.isAuthenticated = true;
                api.setToken(token);
                this.updateUI();
            } catch (error) {
                console.error('Failed to parse user data:', error);
                this.logout();
            }
        }
    }

    async login(email, password) {
        try {
            const response = await api.login(email, password);
            
            if (response.success) {
                this.currentUser = response.user;
                this.isAuthenticated = true;
                api.setToken(response.token || 'dummy-token'); // In real app, get actual token
                
                localStorage.setItem('user_data', JSON.stringify(response.user));
                localStorage.setItem('auth_token', 'dummy-token');
                
                this.updateUI();
                showToast('Login successful!', 'success');
                
                return true;
            }
        } catch (error) {
            showToast(error.message || 'Login failed', 'error');
            return false;
        }
    }

    async register(username, email, password) {
        try {
            const response = await api.register(username, email, password);
            
            if (response.success) {
                this.currentUser = response.user;
                this.isAuthenticated = true;
                api.setToken(response.token || 'dummy-token');
                
                localStorage.setItem('user_data', JSON.stringify(response.user));
                localStorage.setItem('auth_token', 'dummy-token');
                
                this.updateUI();
                showToast('Registration successful!', 'success');
                
                return true;
            }
        } catch (error) {
            showToast(error.message || 'Registration failed', 'error');
            return false;
        }
    }

    async logout() {
        try {
            await api.logout();
        } catch (error) {
            console.error('Logout error:', error);
        }
        
        this.currentUser = null;
        this.isAuthenticated = false;
        api.clearToken();
        
        localStorage.removeItem('user_data');
        localStorage.removeItem('auth_token');
        
        this.updateUI();
        showToast('Logged out successfully', 'success');
    }

    updateUI() {
        const loginBtn = document.getElementById('loginBtn');
        const userMenu = document.getElementById('userMenu');
        
        if (this.isAuthenticated && this.currentUser) {
            if (loginBtn) {
                loginBtn.innerHTML = `
                    <i class="fas fa-user"></i>
                    <span>${this.currentUser.username}</span>
                    <i class="fas fa-chevron-down"></i>
                `;
                loginBtn.classList.add('user-menu-btn');
                loginBtn.onclick = () => this.showUserMenu();
            }
            
            // Update user menu
            if (userMenu) {
                userMenu.innerHTML = `
                    <div class="user-dropdown">
                        <div class="user-info">
                            <div class="user-avatar">${this.currentUser.username.charAt(0).toUpperCase()}</div>
                            <div>
                                <div class="user-name">${this.currentUser.username}</div>
                                <div class="user-email">${this.currentUser.email}</div>
                            </div>
                        </div>
                        <div class="user-menu-items">
                            <button class="user-menu-item" onclick="auth.showProfile()">
                                <i class="fas fa-user"></i> Profile
                            </button>
                            <button class="user-menu-item" onclick="auth.showSettings()">
                                <i class="fas fa-cog"></i> Settings
                            </button>
                            <button class="user-menu-item" onclick="auth.showNotifications()">
                                <i class="fas fa-bell"></i> Notifications
                                <span class="badge" id="notificationBadge">0</span>
                            </button>
                            <button class="user-menu-item logout" onclick="auth.logout()">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </button>
                        </div>
                    </div>
                `;
            }
            
            // Load dashboard data
            loadDashboard();
        } else {
            if (loginBtn) {
                loginBtn.innerHTML = 'Login';
                loginBtn.classList.remove('user-menu-btn');
                loginBtn.onclick = () => showAuthModal();
            }
            
            if (userMenu) {
                userMenu.innerHTML = '';
            }
            
            // Show auth required message
            document.querySelectorAll('.auth-required').forEach(el => {
                el.style.display = 'none';
            });
        }
    }

    showProfile() {
        const modal = document.getElementById('profileModal');
        const profileInfo = document.getElementById('profileInfo');
        
        if (profileInfo) {
            profileInfo.innerHTML = `
                <div class="profile-header">
                    <div class="profile-avatar">
                        ${this.currentUser.username.charAt(0).toUpperCase()}
                    </div>
                    <div class="profile-name">${this.currentUser.username}</div>
                    <div class="profile-email">${this.currentUser.email}</div>
                </div>
                
                <div class="profile-stats">
                    <div class="stat">
                        <div class="stat-value">${this.currentUser.age || '--'}</div>
                        <div class="stat-label">Age</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${this.currentUser.weight || '--'} kg</div>
                        <div class="stat-label">Weight</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${this.currentUser.height || '--'} cm</div>
                        <div class="stat-label">Height</div>
                    </div>
                </div>
                
                <form id="profileForm" class="profile-form">
                    <div class="form-group">
                        <label>Bio</label>
                        <textarea id="profileBio">${this.currentUser.bio || ''}</textarea>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Age</label>
                            <input type="number" id="profileAge" value="${this.currentUser.age || ''}">
                        </div>
                        <div class="form-group">
                            <label>Weight (kg)</label>
                            <input type="number" id="profileWeight" value="${this.currentUser.weight || ''}">
                        </div>
                        <div class="form-group">
                            <label>Height (cm)</label>
                            <input type="number" id="profileHeight" value="${this.currentUser.height || ''}">
                        </div>
                        <div class="form-group">
                            <label>Gender</label>
                            <select id="profileGender">
                                <option value="male" ${this.currentUser.gender === 'male' ? 'selected' : ''}>Male</option>
                                <option value="female" ${this.currentUser.gender === 'female' ? 'selected' : ''}>Female</option>
                                <option value="other" ${this.currentUser.gender === 'other' ? 'selected' : ''}>Other</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Update Profile</button>
                </form>
            `;
            
            // Add form submission handler
            const profileForm = document.getElementById('profileForm');
            if (profileForm) {
                profileForm.onsubmit = async (e) => {
                    e.preventDefault();
                    
                    const data = {
                        bio: document.getElementById('profileBio').value,
                        age: parseInt(document.getElementById('profileAge').value) || null,
                        weight: parseFloat(document.getElementById('profileWeight').value) || null,
                        height: parseFloat(document.getElementById('profileHeight').value) || null,
                        gender: document.getElementById('profileGender').value
                    };
                    
                    try {
                        const response = await api.updateProfile(data);
                        if (response.success) {
                            this.currentUser = response.user;
                            localStorage.setItem('user_data', JSON.stringify(response.user));
                            showToast('Profile updated successfully', 'success');
                            this.showProfile(); // Refresh
                        }
                    } catch (error) {
                        showToast(error.message || 'Update failed', 'error');
                    }
                };
            }
        }
        
        modal.classList.add('active');
    }

    showSettings() {
        // Implementation for settings modal
        showToast('Settings feature coming soon', 'info');
    }

    showNotifications() {
        const panel = document.getElementById('notificationsPanel');
        panel.classList.add('active');
        updateNotifications();
    }

    showUserMenu() {
        const userMenu = document.querySelector('.user-dropdown');
        if (userMenu) {
            userMenu.style.display = userMenu.style.display === 'block' ? 'none' : 'block';
        }
    }
}

// Create global auth instance
const auth = new AuthManager();

// Utility Functions
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    else if (type === 'error') icon = 'exclamation-circle';
    else if (type === 'warning') icon = 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <div class="toast-content">
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showAuthModal() {
    const modal = document.getElementById('authModal');
    modal.classList.add('active');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
    
    document.querySelectorAll('.user-dropdown').forEach(dropdown => {
        dropdown.style.display = 'none';
    });
}

function closeNotifications() {
    const panel = document.getElementById('notificationsPanel');
    panel.classList.remove('active');
}

async function updateNotifications() {
    try {
        const response = await api.getNotifications(true, 10);
        if (response.success) {
            const list = document.getElementById('notificationsList');
            const badge = document.getElementById('notificationBadge');
            
            if (badge) {
                badge.textContent = response.unread_count || '0';
            }
            
            if (list) {
                if (response.notifications.length === 0) {
                    list.innerHTML = '<div class="no-notifications">No new notifications</div>';
                } else {
                    list.innerHTML = response.notifications.map(notification => `
                        <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                             onclick="markNotificationRead(${notification.id})">
                            <div class="notification-title">${notification.title}</div>
                            <div class="notification-message">${notification.message}</div>
                            <div class="notification-time">
                                ${new Date(notification.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </div>
                        </div>
                    `).join('');
                }
            }
        }
    } catch (error) {
        console.error('Failed to update notifications:', error);
    }
}

async function markNotificationRead(notificationId) {
    try {
        await api.markNotificationRead(notificationId);
        updateNotifications();
    } catch (error) {
        console.error('Failed to mark notification read:', error);
    }
}

// Initialize auth UI on page load
document.addEventListener('DOMContentLoaded', () => {
    // Close modals when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.modal-content') && !e.target.closest('.btn') && !e.target.closest('.user-menu-btn')) {
            closeModal();
        }
        
        if (!e.target.closest('.notifications-panel') && !e.target.closest('.fa-bell')) {
            closeNotifications();
        }
    });
    
    // Close buttons
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.onclick = closeModal;
    });
    
    document.querySelectorAll('.close-notifications').forEach(btn => {
        btn.onclick = closeNotifications;
    });
    
    // Auth tab switching
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.onclick = () => {
            const tabName = tab.getAttribute('data-tab');
            
            document.querySelectorAll('.auth-tab').forEach(t => {
                t.classList.remove('active');
            });
            tab.classList.add('active');
            
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.remove('active');
            });
            document.getElementById(`${tabName}Form`).classList.add('active');
        };
    });
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.onsubmit = async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            const success = await auth.login(email, password);
            if (success) {
                closeModal();
            }
        };
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.onsubmit = async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('registerUsername').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            
            const success = await auth.register(username, email, password);
            if (success) {
                closeModal();
            }
        };
    }
});