// API endpoints
const API_BASE_URL = 'http://localhost:3000'; // Update this to match your server's URL
const API_ENDPOINTS = {
    login: `${API_BASE_URL}/auth/login`,
    users: `${API_BASE_URL}/api/users`,
    courses: `${API_BASE_URL}/api/courses`,
    exams: `${API_BASE_URL}/api/exams`,
    questions: `${API_BASE_URL}/api/questions`
};

let currentUser = null;
let authToken = null;

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in (token in localStorage)
    const savedToken = localStorage.getItem('authToken');
    if (savedToken) {
        authToken = savedToken;
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        handleSuccessfulLogin(userData, savedToken);
    }

    // Login functionality
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Add buttons
    document.getElementById('add-user-btn').addEventListener('click', () => showUserForm());
    document.getElementById('add-course-btn').addEventListener('click', () => showCourseForm());
    document.getElementById('add-exam-btn').addEventListener('click', () => showExamForm());
    document.getElementById('add-question-btn').addEventListener('click', () => showQuestionForm());
    
    // Modal close
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    
    // Initialize with login screen if not logged in
    if (!authToken) {
        document.getElementById('app-container').classList.add('hidden');
        document.getElementById('login-container').classList.remove('hidden');
    } else {
        switchTab('users');
    }
});

async function handleLogin() {
    const username = document.getElementById('username-input').value;
    const password = document.getElementById('password-input').value;
    
    try {
        const response = await fetch(API_ENDPOINTS.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            throw new Error('Login failed');
        }
        
        const data = await response.json();
        handleSuccessfulLogin(data.user, data.token);
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

function handleSuccessfulLogin(user, token) {
    currentUser = user;
    authToken = token;
    
    // Save to localStorage for persistence
    localStorage.setItem('authToken', token);
    localStorage.setItem('userData', JSON.stringify(user));
    
    document.getElementById('login-container').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');
    
    if (user.role === 'admin') {
        document.body.classList.add('admin');
    } else {
        document.body.classList.remove('admin');
    }
    
    document.getElementById('current-role').textContent = `Logged in as: ${user.role} (${user.username})`;
    switchTab('users');
}

function handleLogout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    document.getElementById('app-container').classList.add('hidden');
    document.getElementById('login-container').classList.remove('hidden');
    document.body.classList.remove('admin');
}

function switchTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === `${tabName}-tab`) {
            content.classList.add('active');
        }
    });
    
    // Load data for the tab
    loadData();
}

async function loadData() {
    if (!authToken) return;
    
    const activeTab = document.querySelector('.tab-content.active').id;
    
    try {
        switch(activeTab) {
            case 'users-tab':
                await fetchAndRenderUsers();
                break;
            case 'courses-tab':
                await fetchAndRenderCourses();
                break;
            case 'exams-tab':
                await fetchAndRenderExams();
                break;
            case 'questions-tab':
                await fetchAndRenderQuestions();
                break;
        }
    } catch (error) {
        console.error('Error loading data:', error);
        if (error.status === 401) {
            // Token expired or invalid
            handleLogout();
            alert('Your session has expired. Please log in again.');
        } else {
            alert('Error loading data. Please try again.');
        }
    }
}

// API request helper
async function apiRequest(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
        const error = new Error('API request failed');
        error.status = response.status;
        throw error;
    }
    
    return response.json();
}

// Users CRUD operations
async function fetchAndRenderUsers() {
    const users = await apiRequest(API_ENDPOINTS.users);
    const tbody = document.querySelector('#users-table tbody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.user_id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.first_name}</td>
            <td>${user.last_name}</td>
            <td>${user.role}</td>
            <td class="admin-only">
                <button class="edit-btn" data-id="${user.user_id}" data-type="user">Edit</button>
                <button class="delete-btn" data-id="${user.user_id}" data-type="user">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    // Add event listeners to buttons
    addEditDeleteListeners();
}

async function createUser(userData) {
    return apiRequest(API_ENDPOINTS.users, 'POST', userData);
}

async function updateUser(id, userData) {
    return apiRequest(`${API_ENDPOINTS.users}/${id}`, 'PUT', userData);
}

async function deleteUser(id) {
    return apiRequest(`${API_ENDPOINTS.users}/${id}`, 'DELETE');
}

// Courses CRUD operations
async function fetchAndRenderCourses() {
    const [courses, users] = await Promise.all([
        apiRequest(API_ENDPOINTS.courses),
        apiRequest(API_ENDPOINTS.users)
    ]);
    
    const tbody = document.querySelector('#courses-table tbody');
    tbody.innerHTML = '';
    
    courses.forEach(course => {
        const createdByUser = users.find(u => u.user_id === course.created_by);
        const createdByName = createdByUser ? `${createdByUser.first_name} ${createdByUser.last_name}` : course.created_by;
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${course.course_id}</td>
            <td>${course.course_code}</td>
            <td>${course.course_name}</td>
            <td>${course.description || ''}</td>
            <td>${createdByName}</td>
            <td>${course.is_active ? 'Yes' : 'No'}</td>
            <td class="admin-only">
                <button class="edit-btn" data-id="${course.course_id}" data-type="course">Edit</button>
                <button class="delete-btn" data-id="${course.course_id}" data-type="course">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    addEditDeleteListeners();
}

async function createCourse(courseData) {
    return apiRequest(API_ENDPOINTS.courses, 'POST', courseData);
}

async function updateCourse(id, courseData) {
    return apiRequest(`${API_ENDPOINTS.courses}/${id}`, 'PUT', courseData);
}

async function deleteCourse(id) {
    return apiRequest(`${API_ENDPOINTS.courses}/${id}`, 'DELETE');
}

// Exams CRUD operations
async function fetchAndRenderExams() {
    const exams = await apiRequest(API_ENDPOINTS.exams);
    const tbody = document.querySelector('#exams-table tbody');
    tbody.innerHTML = '';
    
    exams.forEach(exam => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${exam.exam_id}</td>
            <td>${exam.course_id}</td>
            <td>${exam.exam_name}</td>
            <td>${exam.time_limit_minutes || ''} min</td>
            <td>${exam.is_published ? 'Yes' : 'No'}</td>
            <td>${exam.is_active ? 'Yes' : 'No'}</td>
            <td class="admin-only">
                <button class="edit-btn" data-id="${exam.exam_id}" data-type="exam">Edit</button>
                <button class="delete-btn" data-id="${exam.exam_id}" data-type="exam">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    addEditDeleteListeners();
}

async function createExam(examData) {
    return apiRequest(API_ENDPOINTS.exams, 'POST', examData);
}

async function updateExam(id, examData) {
    return apiRequest(`${API_ENDPOINTS.exams}/${id}`, 'PUT', examData);
}

async function deleteExam(id) {
    return apiRequest(`${API_ENDPOINTS.exams}/${id}`, 'DELETE');
}

// Questions CRUD operations
async function fetchAndRenderQuestions() {
    const questions = await apiRequest(API_ENDPOINTS.questions);
    const tbody = document.querySelector('#questions-table tbody');
    tbody.innerHTML = '';
    
    questions.forEach(question => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${question.question_id}</td>
            <td>${question.exam_id}</td>
            <td>${question.question_text}</td>
            <td>${question.question_type}</td>
            <td>${question.points}</td>
            <td class="admin-only">
                <button class="edit-btn" data-id="${question.question_id}" data-type="question">Edit</button>
                <button class="delete-btn" data-id="${question.question_id}" data-type="question">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    addEditDeleteListeners();
}

async function createQuestion(questionData) {
    return apiRequest(API_ENDPOINTS.questions, 'POST', questionData);
}

async function updateQuestion(id, questionData) {
    return apiRequest(`${API_ENDPOINTS.questions}/${id}`, 'PUT', questionData);
}

async function deleteQuestion(id) {
    return apiRequest(`${API_ENDPOINTS.questions}/${id}`, 'DELETE');
}

function addEditDeleteListeners() {
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = parseInt(e.target.dataset.id);
            const type = e.target.dataset.type;
            
            try {
                switch(type) {
                    case 'user':
                        const user = await apiRequest(`${API_ENDPOINTS.users}/${id}`);
                        editUser(user);
                        break;
                    case 'course':
                        const course = await apiRequest(`${API_ENDPOINTS.courses}/${id}`);
                        editCourse(course);
                        break;
                    case 'exam':
                        const exam = await apiRequest(`${API_ENDPOINTS.exams}/${id}`);
                        editExam(exam);
                        break;
                    case 'question':
                        const question = await apiRequest(`${API_ENDPOINTS.questions}/${id}`);
                        editQuestion(question);
                        break;
                }
            } catch (error) {
                console.error(`Error fetching ${type}:`, error);
                alert(`Error loading ${type} data. Please try again.`);
            }
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = parseInt(e.target.dataset.id);
            const type = e.target.dataset.type;
            
            if (confirm(`Are you sure you want to delete this ${type}?`)) {
                try {
                    switch(type) {
                        case 'user':
                            await deleteUser(id);
                            break;
                        case 'course':
                            await deleteCourse(id);
                            break;
                        case 'exam':
                            await deleteExam(id);
                            break;
                        case 'question':
                            await deleteQuestion(id);
                            break;
                    }
                    
                    // Reload data after successful deletion
                    loadData();
                    alert(`${type.charAt(0).toUpperCase() + type.slice(1)} successfully deleted`);
                } catch (error) {
                    console.error(`Error deleting ${type}:`, error);
                    alert(`Error deleting ${type}. Please try again.`);
                }
            }
        });
    });
}

// Form handling functions
async function showUserForm(user = null) {
    const isEdit = user !== null;
    const title = isEdit ? 'Edit User' : 'Add User';
    
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div>
            <label for="username">Username</label>
            <input type="text" id="username" value="${user?.username || ''}" required ${isEdit ? 'readonly' : ''}>
        </div>
        <div>
            <label for="email">Email</label>
            <input type="email" id="email" value="${user?.email || ''}" required>
        </div>
        <div>
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" value="${user?.first_name || ''}" required>
        </div>
        <div>
            <label for="last_name">Last Name</label>
            <input type="text" id="last_name" value="${user?.last_name || ''}" required>
        </div>
        <div>
            <label for="role">Role</label>
            <select id="role" required>
                <option value="admin" ${user?.role === 'admin' ? 'selected' : ''}>Admin</option>
                <option value="professor" ${user?.role === 'professor' ? 'selected' : ''}>Professor</option>
                <option value="student" ${user?.role === 'student' ? 'selected' : ''}>Student</option>
            </select>
        </div>
        ${!isEdit ? `
        <div>
            <label for="password">Password</label>
            <input type="password" id="password" required>
        </div>` : ''}
        <div class="form-actions">
            <button type="button" class="cancel-btn">Cancel</button>
            <button type="submit">${isEdit ? 'Update' : 'Create'}</button>
        </div>
    `;
    
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal').classList.remove('hidden');
    
    // Add form submit handler
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const userData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            role: document.getElementById('role').value
        };
        
        // Add password for new users
        if (!isEdit) {
            userData.password = document.getElementById('password').value;
        }
        
        try {
            if (isEdit) {
                await updateUser(user.user_id, userData);
                alert('User updated successfully');
            } else {
                await createUser(userData);
                alert('User created successfully');
            }
            
            closeModal();
            loadData();
        } catch (error) {
            console.error('Error saving user:', error);
            alert(`Error ${isEdit ? 'updating' : 'creating'} user. Please try again.`);
        }
    };
    
    // Add cancel button handler
    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
}

async function showCourseForm(course = null) {
    const isEdit = course !== null;
    const title = isEdit ? 'Edit Course' : 'Add Course';
    
    // Fetch professors for dropdown
    const users = await apiRequest(API_ENDPOINTS.users);
    const professors = users.filter(u => u.role === 'professor');
    
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div>
            <label for="course_code">Course Code</label>
            <input type="text" id="course_code" value="${course?.course_code || ''}" required>
        </div>
        <div>
            <label for="course_name">Course Name</label>
            <input type="text" id="course_name" value="${course?.course_name || ''}" required>
        </div>
        <div>
            <label for="description">Description</label>
            <textarea id="description">${course?.description || ''}</textarea>
        </div>
        <div>
            <label for="created_by">Created By</label>
            <select id="created_by" required>
                ${professors.map(p => 
                    `<option value="${p.user_id}" ${course?.created_by === p.user_id ? 'selected' : ''}>
                        ${p.first_name} ${p.last_name}
                    </option>`
                ).join('')}
            </select>
        </div>
        <div>
            <label for="is_active">Active</label>
            <input type="checkbox" id="is_active" ${course?.is_active !== false ? 'checked' : ''}>
        </div>
        <div class="form-actions">
            <button type="button" class="cancel-btn">Cancel</button>
            <button type="submit">${isEdit ? 'Update' : 'Create'}</button>
        </div>
    `;
    
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal').classList.remove('hidden');
    
    // Add form submit handler
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const courseData = {
            course_code: document.getElementById('course_code').value,
            course_name: document.getElementById('course_name').value,
            description: document.getElementById('description').value,
            created_by: parseInt(document.getElementById('created_by').value),
            is_active: document.getElementById('is_active').checked
        };
        
        try {
            if (isEdit) {
                await updateCourse(course.course_id, courseData);
                alert('Course updated successfully');
            } else {
                await createCourse(courseData);
                alert('Course created successfully');
            }
            
            closeModal();
            loadData();
        } catch (error) {
            console.error('Error saving course:', error);
            alert(`Error ${isEdit ? 'updating' : 'creating'} course. Please try again.`);
        }
    };
    
    // Add cancel button handler
    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
}

async function showExamForm(exam = null) {
    const isEdit = exam !== null;
    const title = isEdit ? 'Edit Exam' : 'Add Exam';
    
    // Fetch courses for dropdown
    const courses = await apiRequest(API_ENDPOINTS.courses);
    
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div>
            <label for="course_id">Course</label>
            <select id="course_id" required>
                ${courses.map(c => 
                    `<option value="${c.course_id}" ${exam?.course_id === c.course_id ? 'selected' : ''}>
                        ${c.course_code} - ${c.course_name}
                    </option>`
                ).join('')}
            </select>
        </div>
        <div>
            <label for="exam_name">Exam Name</label>
            <input type="text" id="exam_name" value="${exam?.exam_name || ''}" required>
        </div>
        <div>
            <label for="time_limit_minutes">Time Limit (minutes)</label>
            <input type="number" id="time_limit_minutes" value="${exam?.time_limit_minutes || ''}">
        </div>
        <div>
            <label for="is_published">Published</label>
            <input type="checkbox" id="is_published" ${exam?.is_published ? 'checked' : ''}>
        </div>
        <div>
            <label for="is_active">Active</label>
            <input type="checkbox" id="is_active" ${exam?.is_active !== false ? 'checked' : ''}>
        </div>
        <div class="form-actions">
            <button type="button" class="cancel-btn">Cancel</button>
            <button type="submit">${isEdit ? 'Update' : 'Create'}</button>
        </div>
    `;
    
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal').classList.remove('hidden');
    
    // Add form submit handler
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const examData = {
            course_id: parseInt(document.getElementById('course_id').value),
            exam_name: document.getElementById('exam_name').value,
            time_limit_minutes: parseInt(document.getElementById('time_limit_minutes').value) || null,
            is_published: document.getElementById('is_published').checked,
            is_active: document.getElementById('is_active').checked
        };
        
        try {
            if (isEdit) {
                await updateExam(exam.exam_id, examData);
                alert('Exam updated successfully');
            } else {
                await createExam(examData);
                alert('Exam created successfully');
            }
            
            closeModal();
            loadData();
        } catch (error) {
            console.error('Error saving exam:', error);
            alert(`Error ${isEdit ? 'updating' : 'creating'} exam. Please try again.`);
        }
    };
    
    // Add cancel button handler
    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
}

async function showQuestionForm(question = null) {
    const isEdit = question !== null;
    const title = isEdit ? 'Edit Question' : 'Add Question';
    
    // Fetch exams for dropdown
    const exams = await apiRequest(API_ENDPOINTS.exams);
    
    const form = document.getElementById('modal-form');
    form.innerHTML = `
        <div>
            <label for="exam_id">Exam</label>
            <select id="exam_id" required>
                ${exams.map(e => 
                    `<option value="${e.exam_id}" ${question?.exam_id === e.exam_id ? 'selected' : ''}>
                        ${e.exam_name}
                    </option>`
                ).join('')}
            </select>
        </div>
        <div>
            <label for="question_text">Question Text</label>
            <textarea id="question_text" required>${question?.question_text || ''}</textarea>
        </div>
        <div>
            <label for="question_type">Question Type</label>
            <select id="question_type" required>
                <option value="multiple_choice" ${question?.question_type === 'multiple_choice' ? 'selected' : ''}>Multiple Choice</option>
                <option value="true_false" ${question?.question_type === 'true_false' ? 'selected' : ''}>True/False</option>
                <option value="short_answer" ${question?.question_type === 'short_answer' ? 'selected' : ''}>Short Answer</option>
                <option value="essay" ${question?.question_type === 'essay' ? 'selected' : ''}>Essay</option>
            </select>
        </div>
        <div>
            <label for="points">Points</label>
            <input type="number" id="points" value="${question?.points || 1}" min="1" required>
        </div>
        <div>
            <label for="display_order">Display Order</label>
            <input type="number" id="display_order" value="${question?.display_order || 1}" min="1" required>
        </div>
        <div class="form-actions">
            <button type="button" class="cancel-btn">Cancel</button>
            <button type="submit">${isEdit ? 'Update' : 'Create'}</button>
        </div>
    `;
    
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal').classList.remove('hidden');
    
    // Add form submit handler
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        const questionData = {
            exam_id: parseInt(document.getElementById('exam_id').value),
            question_text: document.getElementById('question_text').value,
            question_type: document.getElementById('question_type').value,
            points: parseInt(document.getElementById('points').value),
            display_order: parseInt(document.getElementById('display_order').value)
        };
        
        try {
            if (isEdit) {
                await updateQuestion(question.question_id, questionData);
                alert('Question updated successfully');
            } else {
                await createQuestion(questionData);
                alert('Question created successfully');
            }
            
            closeModal();
            loadData();
        } catch (error) {
            console.error('Error saving question:', error);
            alert(`Error ${isEdit ? 'updating' : 'creating'} question. Please try again.`);
        }
    };
    
    // Add cancel button handler
    document.querySelector('.cancel-btn').addEventListener('click', closeModal);
}

function editUser(user) {
    if (user) {
        showUserForm(user);
    }
}

function editCourse(course) {
    if (course) {
        showCourseForm(course);
    }
}

function editExam(exam) {
    if (exam) {
        showExamForm(exam);
    }
}

function editQuestion(question) {
    if (question) {
        showQuestionForm(question);
    }
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
    document.getElementById('modal-form').onsubmit = null;
}