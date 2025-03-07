// utils.js

document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('.card');
    let currentStep = 1;
    const totalSteps = parseInt(card.getAttribute('data-total-steps'), 10);
    const promptFile = card.getAttribute('data-prompt-file');

    const backBtn = document.getElementById('backBtn');
    const continueBtn = document.getElementById('continueBtn');
    const progressBar = document.getElementById('progress');
    const copyBtn = document.getElementById('copyBtn');
    const outputResult = document.getElementById('outputResult');
    const inputFields = document.querySelectorAll('textarea, input');

    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
        pedantic: false,
        sanitize: false,
        smartLists: true,
        smartypants: false,
        tables: true
    });

    // Initialize progress bar
    updateProgress();

    // Event Listeners
    continueBtn.addEventListener('click', handleContinue);
    backBtn.addEventListener('click', handleBack);
    if (copyBtn) {
        copyBtn.addEventListener('click', copyToClipboard);
    }

    // Enable "Enter" key to trigger "Continue"
    inputFields.forEach(field => {
        field.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                handleContinue();
            }
        });
    });

    // Function to update the progress bar
    function updateProgress() {
        progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;
    }

    // Function to show the current step
    async function showStep(stepNumber) {
        document.querySelectorAll('.step').forEach(el => {
            el.classList.remove('active');
        });

        const currentStepElement = document.getElementById(`step${stepNumber}`);
        if (currentStepElement) {
            currentStepElement.classList.add('active');
        }

        backBtn.style.display = stepNumber > 1 ? 'inline-block' : 'none';
        continueBtn.style.display = stepNumber < totalSteps ? 'inline-block' : 'none';
        continueBtn.textContent = stepNumber === (totalSteps - 1) ? 'Generate' : 'Continue';

        updateProgress();

        if (stepNumber === totalSteps) {
            await processCurrentStep();
        }
    }

    // Function to handle the Continue button click
    async function handleContinue() {
        if (currentStep < totalSteps) {
            currentStep++;
            await showStep(currentStep);
        }
    }

    // Function to handle the Back button click
    function handleBack() {
        if (currentStep > 1) {
            currentStep--;
            showStep(currentStep);
        }
    }

    // Function to copy the output to the clipboard
    function copyToClipboard() {
        const outputHTML = outputResult.innerHTML;
        const tempTextArea = document.createElement('textarea');
        tempTextArea.value = outputResult.textContent;
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        try {
            document.execCommand('copy');
            alert('Copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        document.body.removeChild(tempTextArea);
    }


    // Function to jsonify the input data
    function jsonifyInput() {
        const inputText = document.getElementById('inputText')?.value || '';
        const keyDetails = document.getElementById('keyDetails')?.value || '';

        const systemPrompt = card.getAttribute('data-system-prompt') || '';
        const model = card.getAttribute('data-model') || '';
        const chatbotName = card.getAttribute('data-chatbot-name') || '';
        const interactionId = document.getElementById('interactionId')?.value || '';

        console.log('inputText:', inputText);
        console.log('keyDetails:', keyDetails);
        console.log('systemPrompt:', systemPrompt);
        console.log('model:', model);
        console.log('interactionId:', interactionId);
        console.log('chatbotName:', chatbotName);

        return {
            "input_text": inputText,
            "system_prompt": systemPrompt,
            "model": model,
            "interaction_id": interactionId,
            "chatbot_name": chatbotName
        };
    }

    // Function to call the API
    async function callAPI() {
        const jsonifiedInput = jsonifyInput();
        console.log('jsonifiedInput:', jsonifiedInput);
        try {
            console.log('Sending to API');
            const response = await fetch('http://127.0.0.1:5000/async_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(jsonifiedInput),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('data:', data.response);
            return data.response;
        } catch (error) {
            console.error('API call failed:', error);
            return { output: `An error occurred while processing your request: ${error.message}` };
        }
    }

   
    // Function to process the current step
    async function processCurrentStep() {
        outputResult.innerHTML = '<div class="loading-spinner"></div>';
        
        try {
            const apiResponse = await callAPI();
            if (apiResponse && apiResponse.status === "success") {
                displayOutput(apiResponse);
            } else {
                outputResult.innerHTML = `<p class="error">${apiResponse?.error || 'Unknown error occurred'}</p>`;
            }
        } catch (error) {
            console.error('API call error:', error);
            outputResult.innerHTML = '<p class="error">Failed to process request</p>';
        }
    }

    // Function to display the API response with Markdown formatting
    function displayOutput(response) {
        if (!response || !response.response) {
            outputResult.innerHTML = '<p class="error">No response received</p>';
            return;
        }

        try {
            const formattedResponse = marked.parse(response.response);
            outputResult.innerHTML = formattedResponse;
        } catch (error) {
            console.error('Markdown parsing error:', error);
            outputResult.innerHTML = `<p>${response.response}</p>`;
        }
    }

    // Initialize the first step
    showStep(currentStep);
});