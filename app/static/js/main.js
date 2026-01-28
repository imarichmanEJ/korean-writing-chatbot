//////////////////////////////////// 이벤트 리스너////////////////////////////////////
// A. 로그인 계정 확인 ( → checkAuthentication )
// B. 로그아웃 버튼 ( 'logoutBtn' → handleLogout )
// C. 사용자 아이콘 드롭다운
// D. 사용자 정보 표시
// E. 사용자 세션 목록 로드 ( → loadSessionList )
// F. 세션 드롭다운 외부 클릭 시 닫기
// G. 사이드바 토글 버튼 ( 'toggleBtn' → (css))
// H. 새 채팅 버튼 ( 'newChatBtn → createNewSession )
// I. 채팅 패널 전송 버튼( 'sendBtn' → sendMessage )
// J. 채팅 입력창 Enter 키 (Shift+Enter는 줄바꿈) ( 'chatInput' → sendMessage )
// K. 추천 버블 버튼 ( 'suggestion-bubble' → sendMessage)
// L. charCount 실시간 업데이트 ('essayAnswerText')
// M. 답안 제출 ('submitBtn' → submitAnswer )
// N. writing-panel 종료 ( 'endBtn' → exitWriting )

document.addEventListener('DOMContentLoaded', async function() {

    // 메인 페이지

    // A. 로그인 계정 확인 ( → checkAuthentication )
    await checkAuthentication();

    // B. 로그아웃 버튼 ( 'logoutBtn' → handleLogout )
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // C. 사용자 아이콘 드롭다운
    const userIconBtn = document.getElementById('userIconBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userIconBtn && userDropdown) {
        userIconBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });
        
        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && e.target !== userIconBtn) {
                userDropdown.classList.remove('active');
            }
        });
    }

    // D. 사용자 정보 표시
    const userId = localStorage.getItem('user_id');
    const username = localStorage.getItem('username');
    const displayUsername = document.getElementById('displayUsername');

    if (displayUsername && username) {
        displayUsername.textContent = username;
    }

    // E. 사용자 세션 목록 로드 ( → loadSessionList )
    if (userId) {
        loadSessionList(userId);
    }

    // F. 세션 드롭다운 외부 클릭 시 닫기
    document.addEventListener('click', () => {
        document.querySelectorAll('.session-dropdown.show').forEach(dd => {
            dd.classList.remove('show');
        });
    });
        
    // G. 사이드바 토글 버튼 ( 'toggleBtn' → (css))
    const toggleBtn = document.getElementById('toggleBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.getElementById('sidebarContainer').classList.toggle('collapsed');
        });
    }   
    
    // H. 새 채팅 버튼 ( 'newChatBtn → createNewSession )
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewSession);
    }
    
    // I. 채팅 패널 전송 버튼( 'sendBtn' → sendMessage )
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            sendMessage();
        });
    }
    
    // J. 채팅 입력창 Enter 키 (Shift+Enter는 줄바꿈) ( 'chatInput' → sendMessage )
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // K. 추천 버블 버튼 ( 'suggestion-bubble' → sendMessage)
    document.querySelectorAll('.suggestion-bubble').forEach(bubble => {
        bubble.addEventListener('click', () => {
            const text = bubble.textContent.trim();
            sendMessage(text);
        });
    });

    // L. charCount 실시간 업데이트 ('essayAnswerText')
    const essayAnswerText = document.getElementById('essayAnswerText');
    if (essayAnswerText) {
        essayAnswerText.addEventListener('input', (e) => {
            const charCount = document.getElementById('charCount');
            if (charCount) {
                charCount.textContent = e.target.value.length;
            }
        });
    }   

    // M. 답안 제출 ('submitBtn' → submitAnswer )
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', submitAnswer);
    }

    // N. writing-panel 종료 ( 'endBtn' → exitWriting )
    const endBtn = document.getElementById('endBtn');
    if (endBtn) {
        endBtn.addEventListener('click', exitWriting);
    }

});

// ============================= (1) 로그인 계정 확인/로그아웃 =============================
// A. 로그인 계정 확인 ( checkAuthentication )
// B. 로그아웃 ( handleLogout )

// A. 로그인 계정 확인 함수
async function checkAuthentication() {

    const token = localStorage.getItem('token');

    if (!token) {
        window.location.href = '/';
        return;
    }
    
    try {
        const response = await fetch('/auth/check', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        
        const data = await response.json();
        
        if (!data.authenticated) {
            throw new Error('Not authenticated');
        }
                
    } catch (error) {
        console.error('인증 실패:', error);
        localStorage.clear();
        window.location.href = '/';
    }
}

// B. 로그아웃 함수
async function handleLogout() {
    try {
        // 1. 서버에 로그아웃 요청 (선택)
        // await fetch('/auth/logout', { method: 'POST' });
        
        // 2. localStorage 완전 정리
        localStorage.clear();
        
        // 3. 로그인 페이지로 이동
        window.location.href = '/';
        
    } catch (error) {
        console.error('로그아웃 실패:', error);
        
        localStorage.clear();
        window.location.href = '/';
    }
}

// ============================= (2) 사이드바 =============================
// A. async function : 새로운 세션 생성( createNewSession → restChatArea, loadSessionList )
// B. async function : 세션 데이터 불러오기( loadSessionList → renderSessionList or renderEmptySessionList )
// C. function : 세션 없을 때 기본값 ( renderEmptySessionList )
// D. function : 세션 목록 불러오기 ( renderSessionList → loadSession )
// E. async function : 특정 세션 데이터 불러오기 ( loadSession → renderMessages )
// F. function : 채팅 화면에 메세지 렌더링 ( renderMessages → displayMessage)
// G. async function : 세션 제목 수정 
// H. async function 세션 삭제


// A. 새로운 세션 생성
async function createNewSession() {
    const userId = localStorage.getItem('user_id');
    const currentSessionId = localStorage.getItem('current_session_id');

    // 1. 채팅 영역 초기화
    resetChatArea();
    
    // 2. 채팅 입력창 초기화
    document.getElementById('chatInput').value = '';
    
    // 3. writing-panel 닫기
    const writingPanel = document.getElementById('writingPanel');
    const chatContainer = document.getElementById('chatContainer');
    
    if (!writingPanel.classList.contains('hidden')) {
        writingPanel.classList.add('hidden');
        chatContainer.classList.remove('panel-active');
    }
    
    // 4. localStorage 정리
    const preservedUserId = localStorage.getItem('user_id');
    localStorage.clear();
    localStorage.setItem('user_id', preservedUserId);
    
    // 5. 추천 버블 다시 표시
    const suggestionBubbles = document.querySelectorAll('.suggestion-bubble');
    suggestionBubbles.forEach(bubble => {
        bubble.style.display = 'inline-flex';
    });
    
    // 6. 현재 세션이 있으면 목록 갱신
    if (currentSessionId && userId) {
        await loadSessionList(userId);
    }
    
    // 7. 모든 세션 active 해제
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
}


// B. 세션 데이터 불러오기
async function loadSessionList(userId) {
    try {
        const response = await fetch(`/sessions/user/${userId}`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.sessions && data.sessions.length > 0) {
            renderSessionList(data.sessions);
        } else {
            renderEmptySessionList();
        }
        
    } catch (error) {
        console.error('세션 목록 로드 에러:', error);
        renderEmptySessionList();
    }
}

// C. 세션 없을 때 기본값
function renderEmptySessionList() {
    const sessionListDiv = document.getElementById('sessionList');
    sessionListDiv.innerHTML = '';
}

// D. 세션 목록 불러오기
function renderSessionList(sessions) {
    const sessionListDiv = document.getElementById('sessionList');
    sessionListDiv.innerHTML = '';
    
    const currentSessionId = localStorage.getItem('current_session_id');
    
    sessions.forEach(session => {

        const sessionItem = document.createElement('div');
        sessionItem.className = 'session-item';

        if (session.session_id === currentSessionId) {
            sessionItem.classList.add('active');
        }

        //세션 제목
        const title = document.createElement('span');
        title.className = 'session-title';
        title.textContent = session.title || 'new chat';

        //메뉴 버튼
        const menuBtn = document.createElement('button');
        menuBtn.className = 'menu-btn';
        menuBtn.type = 'button';
        menuBtn.innerHTML = '⋮';

        //드롭다운
        const dropdown = document.createElement('div');
        dropdown.className = 'session-dropdown';
        
        //이름변경 버튼
        const renameBtn = document.createElement('button');
        renameBtn.className = 'dropdown-item';
        renameBtn.type = 'button';
        renameBtn.textContent = '이름 변경';

        //삭제 버튼
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'dropdown-item delete';
        deleteBtn.type = 'button';
        deleteBtn.textContent = '삭제';

        dropdown.appendChild(renameBtn);
        dropdown.appendChild(deleteBtn);

        //메뉴 버튼 드롭다운
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // 다른 드롭다운 닫기
            document.querySelectorAll('.session-dropdown.show').forEach(dd => {
                if (dd !== dropdown) {
                    dd.classList.remove('show');
                }
            });
            
            dropdown.classList.toggle('show');
        });

        //세션 이름 변경
        renameBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            dropdown.classList.remove('show');
            await editSessionTitle(session.session_id, session.user_id, title);
        });

        //세션 삭제
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();  // 세션 로드 방지
            dropdown.classList.remove('show');

            if (confirm('정말 삭제하시겠습니까?')) {
                await deleteSession(session.session_id, session.user_id);            
            }
        });

        //세션 클릭
        sessionItem.addEventListener('click', () => {
            loadSession(session.session_id, session.user_id);
        });

        sessionItem.appendChild(title);
        sessionItem.appendChild(menuBtn);
        sessionItem.appendChild(dropdown);
        sessionListDiv.appendChild(sessionItem);
    });
}

// E. 특정 세션 데이터 불러오기
async function loadSession(sessionId, userId) {

    const writingPanel = document.getElementById('writingPanel');
    if (writingPanel && !writingPanel.classList.contains('hidden')) {
            exitWriting();
        }
        
    try {
        
        // 모든 session-item inactive
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 클릭한 항목 active
        const clickedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (clickedItem) {
            clickedItem.classList.add('active');
        }
        
        // 세션 메시지 불러오기
        const response = await fetch(`/sessions/${sessionId}/messages?user_id=${userId}`, {
            method: 'GET',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success && data.messages) {
            activateChatArea();
            renderMessages(data.messages);
        }
        
        // 현재 세션 ID 저장
        localStorage.setItem('current_session_id', sessionId);
        
    } catch (error) {
        console.error('세션 로드 에러:', error);
    }
}

// F. 채팅 화면에 렌더링
function renderMessages(messages) {
    const chatArea = document.getElementById('chatArea');
    chatArea.innerHTML = '';
    
    messages.forEach(msg => {
        displayMessage(msg.role, msg.content);
    });
    
    // 추천 버블 숨김
    hideSuggestionBubbles();
}

// G. 세션 제목 수정
async function editSessionTitle(sessionId, userId, titleElement) {
    const currentTitle = titleElement.textContent;
    const newTitle = prompt('새 제목을 입력하세요:', currentTitle);
    
    if (!newTitle || newTitle.trim() === '' || newTitle === currentTitle) {
        return;
    }
    
    try {
        const response = await fetch(`/sessions/${sessionId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                title: newTitle.trim(),
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            titleElement.textContent = newTitle.trim();
        } else {
            alert('제목 변경 실패');
        }
        
    } catch (error) {
        console.error('제목 변경 에러:', error);
        alert('제목 변경 중 오류가 발생했습니다.');
    }
}

// H. 세션 삭제
async function deleteSession(sessionId, userId) {
    try {
        const response = await fetch(`/sessions/${sessionId}?user_id=${userId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 현재 세션이면 초기화
            if (localStorage.getItem('current_session_id') === sessionId) {
                localStorage.removeItem('current_session_id');
                resetChatArea();
            }
            
            await loadSessionList(userId);
        }
        
    } catch (error) {
        console.error('세션 삭제 에러:', error);
        alert('세션 삭제 실패');
    }
}


// ============================= (3) 채팅화면 =============================
// A. function : 메세지 출력 (displayMessage)
// B. async function : 메세지 전송 (sendMessage)
//    1. UI 업데이트 (→ activateChatArea, displayMessage, showLoadingMessage, hideSuggestionBubbles)
//    2. localStorage 데이터 저장 (user_id, session_id, question_id, question_type, submission_id, evaluation_id)
//    3. /chat API 호출  ( → fetch , hideaLoadingMessage )
//    4. (newchat인 경우) 세션 처리 (loadSessionList)
//    5. Assistant 응답 출력 (displayMessage)
//    6. task별 처리 ('generation' → showWritingPanel, 'evaluation' → )
// C. 채팅 화면 활성화/숨기기 (activateCharArea, resetChatArea)
// D. 로딩 메세지 출력/숨기기 (showLoadingMessage, hideLoadingMessage)
// E. 버블 처리 (showSuggestionBubbles, hideSuggestionBubbles)

// A. 메세지 출력
function displayMessage(role, content) {
    const chatArea = document.getElementById('chatArea');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    
    chatArea.appendChild(messageDiv);
    
    chatArea.scrollTop = chatArea.scrollHeight;
}

// B. 메시지 전송
async function sendMessage(messageText) {
    const inputField = document.getElementById('chatInput');
    const user_message = messageText || inputField.value.trim();
    
    if (!user_message) {
        return;
    }

    // ============================ 1.UI 업데이트 ============================
    activateChatArea();
    displayMessage('user', user_message);
    inputField.value = '';
    showLoadingMessage();
    //hideSuggestionBubbles();

    // ============================ 2.localStorage 데이터 ============================
    const userId = localStorage.getItem('user_id');
    const sessionId = localStorage.getItem('current_session_id');
    const questionId = localStorage.getItem('current_question_id');
    const submissionId = localStorage.getItem('current_submission_id');
    const evaluationId = localStorage.getItem('current_evaluation_id');
    
    const payload = {
        user_id: userId,
        session_id: sessionId,
        user_message: user_message
    };   
    if (questionId) {
        payload.question_id = questionId;
    }
    if (submissionId) {
        payload.submission_id = submissionId;
    }
    if (evaluationId) {
        payload.evaluation_id = evaluationId;
    }

    try {
        // ============================ 3.API 호출 ============================ 
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        hideLoadingMessage();

        // ============================ 4.세션 처리 ============================ 
        loadSessionList(userId);

        //NewChat 인 경우
        if (data.session_id && data.session_id !== sessionId) {

            localStorage.setItem('current_session_id', data.session_id);   
            loadSessionList(userId);
                       
            // 새로 생긴 세션 active
            setTimeout(() => {
                const newSessionItem = document.querySelector(`[data-session-id="${data.session_id}"]`);
                if (newSessionItem) {
                    document.querySelectorAll('.session-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    newSessionItem.classList.add('active');
                }
            }, 100);
        }
        

        // ============================ 5.Assistant 응답 출력 ============================
        displayMessage('assistant', data.reply);

        // ============================ 6.task별 처리 ============================
        if (data.task === 'generation') {
            showWritingPanel(data)
            localStorage.setItem('current_question_id', data.question_id);
            
        } else if (data.task === 'evaluation') {
            localStorage.setItem('current_submission_id', data.submission_id);
            localStorage.setItem('current_evaluation_id', data.evaluation_id);
            
        } else if (data.task === 'assistant') {
            // 일반 대화 → 추가 처리 없음
        }

    }
    catch (error) {
        hideLoadingMessage();
        console.error('메시지 전송 에러:', error);
        displayMessage('error', '메시지 전송 중 오류가 발생했습니다.');
    }
}

// C. 채팅 화면 활성화/숨기기
function activateChatArea() {
    const chatArea = document.getElementById('chatArea');
    chatArea.classList.add('active');
}
function resetChatArea() {
    const chatArea = document.getElementById('chatArea');
    chatArea.innerHTML = '';
    chatArea.classList.remove('active');
}

// D. 채팅 화면에 로딩 메시지 출력/숨기기
function showLoadingMessage() {
    const chatArea = document.getElementById('chatArea');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingMessage';
    loadingDiv.className = 'message assistant';
    loadingDiv.textContent = '입력 중...';
    chatArea.appendChild(loadingDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}
function hideLoadingMessage() {
    const loadingDiv = document.getElementById('loadingMessage');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// E. 버블 처리
function showSuggestionBubbles() {
    document.getElementById('suggestionBubbles').style.display = 'flex';
}
function hideSuggestionBubbles() {
    document.getElementById('suggestionBubbles').style.display = 'none';
}


// ============================= (4) 문제화면 =============================
// A. 문제 패널 활성화 ( showWritingPanel → showEssayProblem or showBlankProblem )
// B. 논설문 문제 출력 ( showEssayProblem )
// C. 빈칸 채우기 문제 출력( showBlankProblem )
// D. 문제 패널 END 버튼 ( exitWriting → resetWritingPanel, hideWritingPanel )
// E. 문제 패널 초기화( resetWritingPanel )
// F. 문제 패널 숨기기 ( hideWritingPanel )
// G. 문제 패널 Submit 버튼 ( submitAnswer )

const QUESTION_TYPE = {
    ESSAY: ['ArgumentativeWriting', 'ExpositoryWriting'],
    BLANK: 'Fill-in-the-Blank'
};

const BLANK_TYPE_CONFIG = {
    'EMAIL': { 
        image: 'email_form.png',
        fields: ['blank_stakeholder', 'blank_subject', 'blank_body']
    },
    'USER-POST': { 
        image: 'post_form.png',
        fields: ['blank_stakeholder', 'blank_subject', 'blank_body']
    },
    'TEXT-MESSAGES': { 
        image: 'text_form.png',
        fields: ['blank_p1', 'blank_p2']
    },
    'SHORT-PASSAGE': { 
        image: 'passage_form.png',
        fields: ['blank_body']
    }
};

// A. 문제 패널 활성화
function showWritingPanel(data) {

    console.log("=====1.showWritingPanel=====");
    console.log(data.question_type)
    resetWritingPanel()

    const writingPanel = document.getElementById('writingPanel');
    const chatContainer = document.getElementById('chatContainer');
    
    writingPanel.classList.remove('hidden');
    chatContainer.classList.add('panel-active');

    localStorage.setItem('current_question_type', data.question_type);   
    
    if (QUESTION_TYPE.ESSAY.includes(data.question_type)) {
        showEssayProblem(data.question);
    }
    else if (QUESTION_TYPE.BLANK == data.question_type) {
        showBlankProblem(data);
    }
        
}

// B. 논설문 문제 출력
function showEssayProblem(question) {

    const essayProblem = document.getElementById('essayProblem');
    const blankProblem = document.getElementById('blankProblem');

    console.log("====2.showEssayProblem====")

    // 문제 출력
    document.getElementById('essayQuestion').textContent = question;
    
    // 입력창 초기화
    document.getElementById('essayAnswerText').value = '';
    document.getElementById('charCount').textContent = '0';
  
    // 표시
    essayProblem.classList.remove('hidden');
    blankProblem.classList.add('hidden');
}

// C. 빈칸 채우기 문제 출력
function showBlankProblem(data) {

    const essayProblem = document.getElementById('essayProblem');
    const blankProblem = document.getElementById('blankProblem');
    
    console.log("====2.showBlankProblem====")

    // 문제 출력
    if (data.blank_type == "TEXT-MESSAGES") {
        document.getElementById('blank_p1').innerHTML = data.blank_data.blank_p1;
        document.getElementById('blank_p2').innerHTML = data.blank_data.blank_p2;
    }
    else if (data.blank_type == "SHORT-PASSAGE") {
        document.getElementById('blank_body').innerHTML = data.blank_data.blank_body;
    }
    else if (data.blank_type === "EMAIL" || data.blank_type === "USER-POST") {
        document.getElementById('blank_body').innerHTML = data.blank_data.blank_body;
        document.getElementById('blank_stakeholder').innerHTML = data.blank_data.blank_stakeholder;
        document.getElementById('blank_subject').innerHTML = data.blank_data.blank_subject;
    }

    // 문제 이미지
    const image_config = BLANK_TYPE_CONFIG[data.blank_type];
    if (image_config) {

    const imgEl = document.querySelector('#blankProblemBody img');
    if (imgEl) {
        imgEl.src = `/static/images/${image_config.image}`;
    } else {
        console.error('img 태그를 찾을 수 없음');
    }

    image_config.fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.className = data.blank_type.toLowerCase();
        }
    });
}

    // 입력창 초기화
    document.getElementById('blank1').value = '';
    document.getElementById('blank2').value = '';
    
    // 표시
    blankProblem.classList.remove('hidden');
    essayProblem.classList.add('hidden');

}

// D. 답문제 패널 END 버튼
function exitWriting() {
    const essayAnswer = document.getElementById("essayAnswerText").value;
    const blank1Answer = document.getElementById("blank1").value;
    const blank2Answer = document.getElementById("blank2").value;

    if (essayAnswer || blank1Answer || blank2Answer) {
        const confirmExit = window.confirm("이제까지 작성하신 글은 삭제됩니다. 정말 그만 두시겠습니까?");
        if (!confirmExit) {
            return;
        }
    }
    
    resetWritingPanel();
    hideWritingPanel();
    
    // 저장된 문제 정보 제거
    localStorage.removeItem('current_question_id');
    localStorage.removeItem('current_submission_id');
    localStorage.removeItem('current_evaluation_id');
    localStorage.removeItem('current_question_type');
    
    const buttons = document.getElementsByClassName("suggestion-bubble");
    for (let btn of buttons) {
        btn.style.display = "inline-flex";
    }
}

// E. 문제 패널 초기화
function resetWritingPanel() {

    //입력 필드 초기화
    const panel = document.getElementById('writingPanel');
    panel.querySelectorAll('input, textarea').forEach(el => el.value = '');
    
    //문제요소(제목/글자수 등) 초기화
    const textElements = [
        'charCount',        
        'essayQuestion',
        'blank_stakeholder',
        'blank_subject',
        'blank_body',
        'blank_p1',
        'blank_p2'
    ];

    textElements.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '';
    });

    //빈칸이미지 초기화
    const blankImg = document.querySelector('#blankProblemBody img');
    if (blankImg) {
        blankImg.src = '';
    }

}

// F. 문제 패널 숨기기
function hideWritingPanel() {
    const chatContainer = document.getElementById('chatContainer');
    const writingPanel = document.getElementById('writingPanel');
    
    writingPanel.classList.add('hidden');
    chatContainer.classList.remove('panel-active');
}

// G. 문제 패널 Submit 버튼 
async function submitAnswer() {
    const userId = localStorage.getItem('user_id');
    const sessionId = localStorage.getItem('current_session_id');
    const questionId = localStorage.getItem('current_question_id')
    const questionType = localStorage.getItem('current_question_type')

    let answer = '';

    // 답안 제대로 작성했는지 확인
    if (questionType === 'ArgumentativeWriting') {

        answer = document.getElementById("essayAnswerText").value.trim();
        
        if (!answer) {
            alert('답안을 작성해주세요.');
            return;
        }
        
        const charCount = answer.length;
        if (charCount < 600 || charCount > 700) {
            const proceed = confirm(`현재 글자수: ${charCount}자\n600~700자 범위를 벗어났습니다. 그래도 제출하시겠습니까?`);
            if (!proceed) return;
        }

    } else if (questionType === 'Fill-in-the-Blank') {
        const answer_b1 = document.getElementById("blank1").value.trim();
        const answer_b2 = document.getElementById("blank2").value.trim();
        
        if (!answer_b1 || !answer_b2) {
            alert('모든 빈칸을 채워주세요.');
            return;
        }
        
        answer = `(ㄱ): ${answer_b1}\n(ㄴ): ${answer_b2}`;
    }

    const payload = {
        user_id: userId,
        session_id: sessionId,
        question_id: questionId,
        answer: answer
    };

    try {
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        submitBtn.style.border = "none";
        submitBtn.style.borderRadius = "0";
        submitBtn.style.boxShadow = "none";


        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        displayMessage('user', answer);
        displayMessage('assistant', data.reply);

        localStorage.setItem('current_submission_id', data.submission_id)
        localStorage.setItem('current_evaluation_id', data.evaluation_id)
           
    } catch (error) {
        console.error('Submit error:', error);
        alert('답안 제출에 실패했습니다. 다시 시도해주세요.');
        
    } finally {
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit';
        submitBtn.style.border = "1px solid lightgrey";
        submitBtn.style.borderRadius = "20px";
        submitBtn.style.boxShadow = "0 4px 8px rgba(0, 0, 0.4, 0.4)";
    }
}