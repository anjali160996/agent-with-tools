const API_BASE_URL = 'http://localhost:8000/api';

let currentRunId = null;

// Utility functions
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

// Load all sessions
async function loadSessions() {
    const sessionsList = document.getElementById('sessionsList');
    sessionsList.innerHTML = '<p class="loading-text">Loading sessions...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/runs`);
        if (!response.ok) throw new Error('Failed to load sessions');

        const runs = await response.json();
        
        if (runs.length === 0) {
            sessionsList.innerHTML = '<p class="loading-text">No sessions yet. Create a new one to get started!</p>';
            return;
        }

        sessionsList.innerHTML = '';
        runs.forEach(run => {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            if (run.id === currentRunId) {
                sessionItem.classList.add('active');
            }
            
            const summaryPreview = run.summary.length > 50 
                ? run.summary.substring(0, 50) + '...' 
                : run.summary;
            
            sessionItem.innerHTML = `
                <h3>Session ${run.id.substring(0, 8)}...</h3>
                <div class="session-summary">${summaryPreview}</div>
                <div class="session-date">${new Date(run.created_at).toLocaleString()}</div>
            `;
            
            sessionItem.addEventListener('click', () => loadSession(run.id));
            sessionsList.appendChild(sessionItem);
        });
    } catch (error) {
        sessionsList.innerHTML = '<p class="loading-text">Error loading sessions</p>';
        console.error('Error loading sessions:', error);
    }
}

// Reset view to new session state
function resetToNewSessionView() {
    currentRunId = null;
    const summaryInput = document.getElementById('summaryInput');
    summaryInput.value = '';
    summaryInput.readOnly = false;
    summaryInput.classList.remove('readonly');
    
    // Show create session button
    document.getElementById('createSessionContainer').style.display = 'block';
    document.getElementById('runInfo').style.display = 'none';
    
    // Update step 1 title and description
    document.getElementById('step1Title').textContent = 'Create Test Session';
    document.getElementById('step1Description').textContent = 'Provide a summary or context for test question generation:';
    
        // Clear all content
        document.getElementById('questionsList').innerHTML = '';
        document.getElementById('questionsReview').innerHTML = '';
        document.getElementById('answersList').innerHTML = '';
        document.getElementById('answersReview').innerHTML = '';
        document.getElementById('questionsTagging').innerHTML = '';
        document.getElementById('syncResult').innerHTML = '';
    
    // Hide all steps except step 1
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
    document.getElementById('step4').style.display = 'none';
    document.getElementById('step5').style.display = 'none';
    document.getElementById('step6').style.display = 'none';
    document.getElementById('step7').style.display = 'none';
    document.getElementById('viewActualPage').style.display = 'none';
    
    // Update active session in sidebar
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Load a specific session
async function loadSession(runId) {
    try {
        // Hide view actual page if visible
        document.getElementById('viewActualPage').style.display = 'none';
        
        // Fetch run details
        const runResponse = await fetch(`${API_BASE_URL}/runs/${runId}`);
        if (!runResponse.ok) throw new Error('Failed to load session');
        const run = await runResponse.json();

        // Set as current run
        currentRunId = run.id;
        const summaryInput = document.getElementById('summaryInput');
        summaryInput.value = run.summary;
        summaryInput.readOnly = true;
        summaryInput.classList.add('readonly');
        
        // Hide create session button and show run info
        document.getElementById('createSessionContainer').style.display = 'none';
        document.getElementById('runId').textContent = run.id;
        document.getElementById('runCreated').textContent = new Date(run.created_at).toLocaleString();
        
        // Update staging and sync info
        const lastStagingChange = document.getElementById('lastStagingChange');
        const lastSyncDisplay = document.getElementById('lastSyncDisplay');
        
        if (run.last_staging_change_at) {
            lastStagingChange.textContent = new Date(run.last_staging_change_at).toLocaleString();
        } else {
            lastStagingChange.textContent = 'Never';
        }
        
        if (run.last_sync_at) {
            lastSyncDisplay.textContent = new Date(run.last_sync_at).toLocaleString();
        } else {
            lastSyncDisplay.textContent = 'Never';
        }
        
        document.getElementById('runInfo').style.display = 'block';
        
        // Update step 1 title and description
        document.getElementById('step1Title').textContent = 'Session Summary';
        document.getElementById('step1Description').textContent = 'Summary for this session:';
        
        // Always show step 1
        document.getElementById('step1').style.display = 'block';

        // Clear previous content
        document.getElementById('questionsList').innerHTML = '';
        document.getElementById('questionsReview').innerHTML = '';
        document.getElementById('answersList').innerHTML = '';
        document.getElementById('answersReview').innerHTML = '';
        document.getElementById('questionsTagging').innerHTML = '';
        document.getElementById('syncResult').innerHTML = '';

        // Update active session in sidebar
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
            if (item.querySelector('h3').textContent.includes(run.id.substring(0, 8))) {
                item.classList.add('active');
            }
        });

        // Load questions and answers
        await loadQuestionsForReview();
        await loadAnswersForReview();

        // Show appropriate steps
        document.getElementById('step2').style.display = 'block';
        document.getElementById('step3').style.display = 'block';
        
        const questionsResponse = await fetch(`${API_BASE_URL}/runs/${runId}/questions`);
        const questions = await questionsResponse.json();
        const hasApproved = questions.some(q => q.is_approved === true);
        if (hasApproved) {
            document.getElementById('step4').style.display = 'block';
            document.getElementById('step5').style.display = 'block';
        }
        
        // Always show step 6 and step 7 if there are questions
        if (questions.length > 0) {
            document.getElementById('step6').style.display = 'block';
            document.getElementById('step7').style.display = 'block';
            await loadQuestionsForTagging();
            await loadSyncInfo();
        }

        // Scroll to top
        window.scrollTo(0, 0);
        showSuccess('Session loaded successfully!');
    } catch (error) {
        showError(`Error loading session: ${error.message}`);
    }
}

// New Session button handler
document.getElementById('newSessionBtn').addEventListener('click', () => {
    resetToNewSessionView();
});

// Refresh sessions list
document.getElementById('refreshSessionsBtn').addEventListener('click', () => {
    loadSessions();
});

// Load sessions on page load
loadSessions();

// Step 1: Create Run
document.getElementById('createRunBtn').addEventListener('click', async () => {
    const summary = document.getElementById('summaryInput').value.trim();
    if (!summary) {
        showError('Please provide a summary');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/runs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ summary }),
        });

        if (!response.ok) {
            throw new Error('Failed to create session');
        }

        const run = await response.json();
        currentRunId = run.id;

        // Make textarea read-only and update UI
        const summaryInput = document.getElementById('summaryInput');
        summaryInput.readOnly = true;
        summaryInput.classList.add('readonly');
        
        // Hide create session button and show run info
        document.getElementById('createSessionContainer').style.display = 'none';
        document.getElementById('runId').textContent = run.id;
        document.getElementById('runCreated').textContent = new Date(run.created_at).toLocaleString();
        
        // Update staging and sync info
        const lastStagingChange = document.getElementById('lastStagingChange');
        const lastSyncDisplay = document.getElementById('lastSyncDisplay');
        
        if (run.last_staging_change_at) {
            lastStagingChange.textContent = new Date(run.last_staging_change_at).toLocaleString();
        } else {
            lastStagingChange.textContent = 'Never';
        }
        
        if (run.last_sync_at) {
            lastSyncDisplay.textContent = new Date(run.last_sync_at).toLocaleString();
        } else {
            lastSyncDisplay.textContent = 'Never';
        }
        
        document.getElementById('runInfo').style.display = 'block';
        
        // Update step 1 title and description
        document.getElementById('step1Title').textContent = 'Session Summary';
        document.getElementById('step1Description').textContent = 'Summary for this session:';

        // Clear previous content
        document.getElementById('questionsList').innerHTML = '';
        document.getElementById('questionsReview').innerHTML = '';
        document.getElementById('answersList').innerHTML = '';
        document.getElementById('answersReview').innerHTML = '';
        document.getElementById('questionsTagging').innerHTML = '';
        document.getElementById('syncResult').innerHTML = '';

        // Reload sessions list
        await loadSessions();

        // Show step 2
        document.getElementById('step2').style.display = 'block';
        document.getElementById('step3').style.display = 'none';
        document.getElementById('step4').style.display = 'none';
        document.getElementById('step5').style.display = 'none';
        document.getElementById('step6').style.display = 'none';
        document.getElementById('step7').style.display = 'none';
        showSuccess('Session created successfully!');
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
});

// Step 2: Generate Questions
document.getElementById('generateQuestionsBtn').addEventListener('click', async () => {
    if (!currentRunId) {
        showError('Please create a session first');
        return;
    }

    const numQuestions = parseInt(document.getElementById('numQuestions').value) || 5;
    const loadingDiv = document.getElementById('questionsLoading');
    const questionsList = document.getElementById('questionsList');

    loadingDiv.style.display = 'block';
    questionsList.innerHTML = '';

    try {
        const response = await fetch(
            `${API_BASE_URL}/runs/${currentRunId}/generate-questions?num_questions=${numQuestions}`,
            {
                method: 'POST',
            }
        );

        if (!response.ok) {
            throw new Error('Failed to generate questions');
        }

        const questions = await response.json();
        loadingDiv.style.display = 'none';

        // Reload questions for review (this will show all questions including newly generated)
        await loadQuestionsForReview();

        // Show step 3, step 6, and step 7
        document.getElementById('step3').style.display = 'block';
        document.getElementById('step6').style.display = 'block';
        document.getElementById('step7').style.display = 'block';
        await loadQuestionsForTagging();
        await loadSyncInfo(); // Update staging change time
        showSuccess(`Generated ${questions.length} new question(s) successfully!`);
    } catch (error) {
        loadingDiv.style.display = 'none';
        showError(`Error: ${error.message}`);
    }
});

// Step 3: Load Questions for Review
async function loadQuestionsForReview() {
    if (!currentRunId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/runs/${currentRunId}/questions`);
        if (!response.ok) throw new Error('Failed to load questions');

        const questions = await response.json();
        const reviewDiv = document.getElementById('questionsReview');
        reviewDiv.innerHTML = '';

        // Sort questions by ID to maintain consistent ordering
        questions.sort((a, b) => a.id - b.id);

        questions.forEach((q, index) => {
            const serialNumber = index + 1;
            const statusClass = q.is_approved === true ? 'approved' : 
                               q.is_approved === false ? 'rejected' : '';
            const statusBadge = q.is_approved === true ? 'approved' :
                               q.is_approved === false ? 'rejected' : 'pending';
            const statusText = q.is_approved === true ? 'Approved' :
                              q.is_approved === false ? 'Rejected' : 'Pending';

            const reviewItem = document.createElement('div');
            reviewItem.className = `review-item ${statusClass}`;
            reviewItem.innerHTML = `
                <h3>Question ${serialNumber} <span class="system-id">ID: ${q.id}</span> <span class="status-badge ${statusBadge}">${statusText}</span> <span class="llm-badge">Generated by LLM</span></h3>
                <p>${q.question_text}</p>
                <div class="review-actions">
                    <button class="btn btn-approve" onclick="updateQuestionApproval(${q.id}, true)">
                        Approve
                    </button>
                    <button class="btn btn-reject" onclick="updateQuestionApproval(${q.id}, false)">
                        Reject
                    </button>
                </div>
            `;
            reviewDiv.appendChild(reviewItem);
        });
    } catch (error) {
        showError(`Error loading questions: ${error.message}`);
    }
}

// Update Question Approval
window.updateQuestionApproval = async function(questionId, isApproved) {
    try {
        const response = await fetch(`${API_BASE_URL}/questions/${questionId}/approval`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_approved: isApproved }),
        });

        if (!response.ok) throw new Error('Failed to update question approval');

        await loadQuestionsForReview();
        // Reload answers when question approval changes (answers may be auto-unapproved when question is rejected)
        await loadAnswersForReview();
        await loadSyncInfo(); // Update staging change time
        showSuccess(`Question ${isApproved ? 'approved' : 'rejected'} successfully!`);

        // Show step 4 if at least one question is approved
        const questionsResponse = await fetch(`${API_BASE_URL}/runs/${currentRunId}/questions`);
        const questions = await questionsResponse.json();
        const hasApproved = questions.some(q => q.is_approved === true);
        if (hasApproved) {
            document.getElementById('step4').style.display = 'block';
        }
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
};

// Step 4: Generate Answers
document.getElementById('generateAnswersBtn').addEventListener('click', async () => {
    if (!currentRunId) {
        showError('Please create a session first');
        return;
    }

    const loadingDiv = document.getElementById('answersLoading');
    const answersList = document.getElementById('answersList');

    loadingDiv.style.display = 'block';
    answersList.innerHTML = '';

    try {
        const response = await fetch(
            `${API_BASE_URL}/runs/${currentRunId}/generate-answers`,
            {
                method: 'POST',
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate answers');
        }

        const answers = await response.json();
        loadingDiv.style.display = 'none';

        // Reload answers for review (this will show all answers including newly generated)
        await loadAnswersForReview();
        await loadSyncInfo(); // Update staging change time

        // Show step 5
        document.getElementById('step5').style.display = 'block';
        
        if (answers.length === 0) {
            showSuccess('All answers for approved questions have already been generated or are pending.');
        } else {
            showSuccess(`Generated ${answers.length} answer(s) successfully!`);
        }
    } catch (error) {
        loadingDiv.style.display = 'none';
        showError(`Error: ${error.message}`);
    }
});

// Step 5: Load Answers for Review
async function loadAnswersForReview() {
    if (!currentRunId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/runs/${currentRunId}/answers`);
        if (!response.ok) throw new Error('Failed to load answers');

        const answers = await response.json();
        const reviewDiv = document.getElementById('answersReview');
        reviewDiv.innerHTML = '';

        // Get questions for context
        const questionsResponse = await fetch(`${API_BASE_URL}/runs/${currentRunId}/questions`);
        const questions = await questionsResponse.json();
        const questionsMap = {};
        questions.forEach(q => questionsMap[q.id] = q);

        // Sort answers by ID to maintain consistent ordering
        answers.sort((a, b) => a.id - b.id);

        answers.forEach((a, index) => {
            const serialNumber = index + 1;
            const statusClass = a.is_approved === true ? 'approved' : 
                               a.is_approved === false ? 'rejected' : '';
            const statusBadge = a.is_approved === true ? 'approved' :
                               a.is_approved === false ? 'rejected' : 'pending';
            const statusText = a.is_approved === true ? 'Approved' :
                              a.is_approved === false ? 'Rejected' : 'Pending';

            const question = questionsMap[a.question_id];
            const reviewItem = document.createElement('div');
            reviewItem.className = `review-item ${statusClass}`;
            reviewItem.innerHTML = `
                <h3>Answer ${serialNumber} <span class="system-id">ID: ${a.id}</span> <span class="status-badge ${statusBadge}">${statusText}</span> <span class="llm-badge">Generated by LLM</span></h3>
                <div class="answer-context">
                    <strong>Question:</strong> ${question ? question.question_text : 'N/A'}
                </div>
                <p>${a.answer_text}</p>
                <div class="review-actions">
                    <button class="btn btn-approve" onclick="updateAnswerApproval(${a.id}, true)">
                        Approve
                    </button>
                    <button class="btn btn-reject" onclick="updateAnswerApproval(${a.id}, false)">
                        Reject
                    </button>
                </div>
            `;
            reviewDiv.appendChild(reviewItem);
        });
    } catch (error) {
        showError(`Error loading answers: ${error.message}`);
    }
}

// Update Answer Approval
window.updateAnswerApproval = async function(answerId, isApproved) {
    try {
        const response = await fetch(`${API_BASE_URL}/answers/${answerId}/approval`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ is_approved: isApproved }),
        });

        if (!response.ok) throw new Error('Failed to update answer approval');

        await loadAnswersForReview();
        await loadSyncInfo(); // Update staging change time
        showSuccess(`Answer ${isApproved ? 'approved' : 'rejected'} successfully!`);
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
};

// Step 6: Load Questions for Tagging
async function loadQuestionsForTagging() {
    if (!currentRunId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/runs/${currentRunId}/questions`);
        if (!response.ok) throw new Error('Failed to load questions');

        const questions = await response.json();
        const taggingDiv = document.getElementById('questionsTagging');
        taggingDiv.innerHTML = '';

        // Sort questions by ID
        questions.sort((a, b) => a.id - b.id);

        // Load all tags
        const tagsResponse = await fetch(`${API_BASE_URL}/tags`);
        const allTags = tagsResponse.ok ? await tagsResponse.json() : [];

        questions.forEach((q, index) => {
            const serialNumber = index + 1;
            const taggingItem = document.createElement('div');
            taggingItem.className = 'tagging-item';
            taggingItem.innerHTML = `
                <h3>Question ${serialNumber} <span class="system-id">ID: ${q.id}</span></h3>
                <p>${q.question_text}</p>
                <div class="tag-input-container">
                    <label>Add tags (comma-separated):</label>
                    <input type="text" 
                           id="tagInput_${q.id}" 
                           class="tag-input" 
                           placeholder="e.g., beginner, concepts, practical"
                           value="">
                    <button class="btn btn-primary btn-tag" onclick="addQuestionTags(${q.id})">
                        Add Tags
                    </button>
                </div>
                <div id="tagsDisplay_${q.id}" class="tags-display"></div>
            `;
            taggingDiv.appendChild(taggingItem);

            // Load existing tags for this question
            loadQuestionTags(q.id);
        });
    } catch (error) {
        showError(`Error loading questions for tagging: ${error.message}`);
    }
}

// Load tags for a specific question
async function loadQuestionTags(questionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/questions/${questionId}/tags`);
        if (!response.ok) throw new Error('Failed to load tags');

        const tags = await response.json();
        const tagsDisplay = document.getElementById(`tagsDisplay_${questionId}`);
        tagsDisplay.innerHTML = '';

        if (tags.length === 0) {
            tagsDisplay.innerHTML = '<span class="no-tags">No tags assigned</span>';
            return;
        }

        tags.forEach(tag => {
            const tagContainer = document.createElement('span');
            tagContainer.className = 'tag-badge-container';
            tagContainer.innerHTML = `
                <span class="tag-badge">${tag.name}</span>
                <button class="tag-remove-btn" onclick="removeQuestionTag(${questionId}, ${tag.id}, '${tag.name.replace(/'/g, "\\'")}')" title="Remove tag">×</button>
            `;
            tagsDisplay.appendChild(tagContainer);
        });
    } catch (error) {
        console.error(`Error loading tags for question ${questionId}:`, error);
    }
}

// Add tags to a question (adds to existing tags)
window.addQuestionTags = async function(questionId) {
    const tagInput = document.getElementById(`tagInput_${questionId}`);
    const newTagNames = tagInput.value.split(',').map(t => t.trim()).filter(t => t.length > 0);

    if (newTagNames.length === 0) {
        showError('Please enter at least one tag');
        return;
    }

    try {
        // Get existing tags first
        const existingTagsResponse = await fetch(`${API_BASE_URL}/questions/${questionId}/tags`);
        const existingTags = existingTagsResponse.ok ? await existingTagsResponse.json() : [];
        const existingTagNames = existingTags.map(t => t.name.toLowerCase());
        
        // Combine existing tags with new tags, avoiding duplicates
        const allTagNames = [...existingTags.map(t => t.name)];
        newTagNames.forEach(tagName => {
            if (!existingTagNames.includes(tagName.toLowerCase())) {
                allTagNames.push(tagName);
            }
        });

        const response = await fetch(`${API_BASE_URL}/questions/${questionId}/tags`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tag_names: allTagNames }),
        });

        if (!response.ok) throw new Error('Failed to update tags');

        // Reload tags display
        await loadQuestionTags(questionId);
        await loadSyncInfo(); // Update staging change time
        tagInput.value = '';
        showSuccess('Tags added successfully!');
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
};

// Remove a tag from a question
window.removeQuestionTag = async function(questionId, tagId, tagName) {
    try {
        // Get existing tags
        const existingTagsResponse = await fetch(`${API_BASE_URL}/questions/${questionId}/tags`);
        const existingTags = existingTagsResponse.ok ? await existingTagsResponse.json() : [];
        
        // Remove the tag from the list
        const remainingTagNames = existingTags
            .filter(t => t.id !== tagId)
            .map(t => t.name);

        const response = await fetch(`${API_BASE_URL}/questions/${questionId}/tags`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tag_names: remainingTagNames }),
        });

        if (!response.ok) throw new Error('Failed to remove tag');

        // Reload tags display
        await loadQuestionTags(questionId);
        await loadSyncInfo(); // Update staging change time
        showSuccess(`Tag "${tagName}" removed successfully!`);
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
};

// Step 7: Load Sync Info (also updates staging/sync display at top)
async function loadSyncInfo() {
    if (!currentRunId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/runs/${currentRunId}`);
        if (!response.ok) throw new Error('Failed to load run info');

        const run = await response.json();
        
        // Update Step 7 sync info
        const syncInfo = document.getElementById('syncInfo');
        const lastSyncTime = document.getElementById('lastSyncTime');

        if (run.last_sync_at) {
            lastSyncTime.textContent = new Date(run.last_sync_at).toLocaleString();
            syncInfo.style.display = 'block';
        } else {
            syncInfo.style.display = 'none';
        }
        
        // Update top staging/sync info in runInfo section
        const lastStagingChange = document.getElementById('lastStagingChange');
        const lastSyncDisplay = document.getElementById('lastSyncDisplay');
        
        if (lastStagingChange && lastSyncDisplay) {
            if (run.last_staging_change_at) {
                lastStagingChange.textContent = new Date(run.last_staging_change_at).toLocaleString();
            } else {
                lastStagingChange.textContent = 'Never';
            }
            
            if (run.last_sync_at) {
                lastSyncDisplay.textContent = new Date(run.last_sync_at).toLocaleString();
            } else {
                lastSyncDisplay.textContent = 'Never';
            }
        }
    } catch (error) {
        console.error('Error loading sync info:', error);
    }
}

// Step 7: Sync to Actual Tables
document.getElementById('syncToActualBtn').addEventListener('click', async () => {
    if (!currentRunId) {
        showError('Please create a session first');
        return;
    }

    const loadingDiv = document.getElementById('syncLoading');
    const resultDiv = document.getElementById('syncResult');

    loadingDiv.style.display = 'block';
    resultDiv.innerHTML = '';

    try {
        const response = await fetch(
            `${API_BASE_URL}/runs/${currentRunId}/sync-to-actual`,
            {
                method: 'POST',
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to sync to actual tables');
        }

        const result = await response.json();
        loadingDiv.style.display = 'none';

        resultDiv.innerHTML = `
            <div class="success-message">
                <strong>Sync completed!</strong><br>
                Questions synced: ${result.questions_synced}<br>
                Last sync: ${new Date(result.last_sync_at).toLocaleString()}
            </div>
        `;

        await loadSyncInfo();
        showSuccess('Synced to final tables successfully!');
    } catch (error) {
        loadingDiv.style.display = 'none';
        showError(`Error: ${error.message}`);
    }
});

// View Actual Questions
async function loadActualQuestions(filterRunId = null) {
    const questionsList = document.getElementById('actualQuestionsList');
    questionsList.innerHTML = '<p class="loading-text">Loading questions...</p>';

    try {
        const url = filterRunId 
            ? `${API_BASE_URL}/actual/questions?run_id=${filterRunId}`
            : `${API_BASE_URL}/actual/questions`;
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load actual questions');

        const questions = await response.json();
        questionsList.innerHTML = '';

        if (questions.length === 0) {
            questionsList.innerHTML = '<p class="loading-text">No questions found in final tables.</p>';
            return;
        }

        questions.forEach((q, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'actual-question-item';
            
            const tagsHtml = q.tags.length > 0
                ? q.tags.map(tag => `<span class="tag-badge">${tag.name}</span>`).join(' ')
                : '<span class="no-tags">No tags</span>';
            
            const answerHtml = q.answer
                ? `<div class="answer-section"><strong>Answer:</strong> <p>${q.answer.answer_text}</p></div>`
                : '<div class="answer-section"><span class="no-answer">No answer available</span></div>';
            
            const stagingIdText = q.staging_id ? ` (Staging ID: ${q.staging_id})` : '';
            questionDiv.innerHTML = `
                <div class="question-header">
                    <h3>Question ${index + 1} <span class="system-id">ID: ${q.id}${stagingIdText}</span></h3>
                    <div class="question-meta">
                        <span>Session: ${q.run_id.substring(0, 8)}...</span>
                        <span>Created: ${new Date(q.created_at).toLocaleString()}</span>
                    </div>
                </div>
                <p class="question-text">${q.question_text}</p>
                <div class="tags-section">
                    <strong>Tags:</strong> ${tagsHtml}
                </div>
                ${answerHtml}
            `;
            questionsList.appendChild(questionDiv);
        });
    } catch (error) {
        questionsList.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
    }
}

// Load runs for filter dropdown
async function loadRunsForFilter() {
    try {
        const response = await fetch(`${API_BASE_URL}/runs`);
        if (!response.ok) return;

        const runs = await response.json();
        const filterSelect = document.getElementById('filterRunId');
        
        // Keep "All Sessions" option and add runs
        filterSelect.innerHTML = '<option value="">All Sessions</option>';
        runs.forEach(run => {
            const option = document.createElement('option');
            option.value = run.id;
            option.textContent = `${run.id.substring(0, 8)}... - ${run.summary.substring(0, 50)}`;
            filterSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading runs for filter:', error);
    }
}

// View Actual Questions button (from sidebar)
document.getElementById('viewActualBtn').addEventListener('click', async () => {
    // Hide all workflow steps
    document.querySelectorAll('.step').forEach(step => {
        if (step.id !== 'viewActualPage') {
            step.style.display = 'none';
        }
    });
    
    document.getElementById('viewActualPage').style.display = 'block';
    
    await loadRunsForFilter();
    await loadActualQuestions();
    
    window.scrollTo(0, 0);
});

// Filter by run_id
document.getElementById('filterRunId').addEventListener('change', (e) => {
    const runId = e.target.value;
    loadActualQuestions(runId || null);
});

// Refresh actual questions
document.getElementById('refreshActualBtn').addEventListener('click', () => {
    const filterRunId = document.getElementById('filterRunId').value;
    loadActualQuestions(filterRunId || null);
});

// When loading a session or creating new session, hide the view actual page
// This is already handled in resetToNewSessionView() and loadSession()

