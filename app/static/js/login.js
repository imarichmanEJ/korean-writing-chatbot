
document.addEventListener('DOMContentLoaded', async function() {

    // 로그인 페이지
    console.log('로그인 페이지');

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

});


async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('login-username').value.trim();
    
    if (!username) {
        alert('이름을 입력해주세요!');
        return;
    }
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username })
        });

        if (!response.ok) {
            const text = await response.text();
            console.error('Server error:', text);
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            localStorage.clear();
            localStorage.setItem('token', data.token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            
            window.location.href = '/main';
        } else {
            alert(data.message);
        }
        
    } catch (error) {
        console.error('로그인 에러:', error);
        showMessage('로그인 중 오류가 발생했습니다.', 'error');
    }
}


