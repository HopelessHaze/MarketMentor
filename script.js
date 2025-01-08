// Dynamic Title Animation
const dynamicTitle = document.querySelector('.dynamic-title');

// Define words to animate in the title
const titleWords = ['Welcome to MarketMentor', 'The Walmart Supplier AI Assistant', 'Try it Now'];
let titleIndex = 0;

function changeTitleWord() {
    dynamicTitle.textContent = titleWords[titleIndex];
    titleIndex = (titleIndex + 1) % titleWords.length; // Cycle through words
}

// Update the title every 3 seconds
setInterval(changeTitleWord, 3000);

// Scroll to Sections on Navigation Click
const navLinks = document.querySelectorAll('nav .menu li a');

navLinks.forEach(link => {
    link.addEventListener('click', event => {
        event.preventDefault();
        const targetId = event.target.getAttribute('href').substring(1); // Get target section ID
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            window.scrollTo({
                top: targetSection.offsetTop - 80, // Adjust for header height
                behavior: 'smooth'
            });
        }
    });
});

// Highlight Active Review (Optional Carousel)
const reviewTiles = document.querySelectorAll('.review');
let activeReviewIndex = 0;

function highlightNextReview() {
    // Remove active state from the current review
    reviewTiles[activeReviewIndex].classList.remove('active');

    // Move to the next review
    activeReviewIndex = (activeReviewIndex + 1) % reviewTiles.length;

    // Highlight the next review
    reviewTiles[activeReviewIndex].classList.add('active');
}

// Automatically switch highlighted reviews every 5 seconds
setInterval(highlightNextReview, 5000);

// Add hover interaction to review tiles
reviewTiles.forEach(tile => {
    tile.addEventListener('mouseover', () => {
        tile.style.transform = 'scale(1.05)';
    });

    tile.addEventListener('mouseout', () => {
        tile.style.transform = 'scale(1)';
    });
});

// Contact Us Form Animation
const submitButton = document.querySelector('.contact-us button[type="submit"]');

if (submitButton) {
    submitButton.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent default form submission for testing
        submitButton.style.transform = 'scale(0.95)';
        setTimeout(() => {
            submitButton.style.transform = 'scale(1)';
        }, 150); // Restore scale after 150ms
        alert('Thank you! Your message has been sent.'); // Simulate form submission feedback
    });
}

// Smooth Scroll to Contact Us Section on "Get Started" Button Click
const getStartedButton = document.querySelector('.hero .cta');

if (getStartedButton) {
    getStartedButton.addEventListener('click', (event) => {
        event.preventDefault();
        const chatGPTSection = document.getElementById('ask-chatgpt-section');
        if (chatGPTSection) {
            chatGPTSection.style.display = 'block'; // Reveal the "Ask ChatGPT" section
            window.scrollTo({
                top: chatGPTSection.offsetTop - 80, // Adjust for header height
                behavior: 'smooth'
            });
        }
    });
}

// Animate Contact Us Text Area on Focus
const contactTextarea = document.querySelector('.contact-us textarea');

if (contactTextarea) {
    contactTextarea.addEventListener('focus', () => {
        contactTextarea.style.boxShadow = '0 0 15px var(--text-gradient-start)';
    });

    contactTextarea.addEventListener('blur', () => {
        contactTextarea.style.boxShadow = 'none';
    });
}

// =========================
// ChatGPT Search Bar Logic with OpenRouter
// =========================

// DOM Elements for ChatGPT Search Bar
const searchInput = document.getElementById('chatgpt-query');
const searchButton = document.getElementById('search-btn');
const searchResults = document.getElementById('search-results');

// Function to handle ChatGPT query using OpenRouter
async function handleSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        searchResults.style.display = 'block';
        searchResults.innerHTML = `<p>Please enter a question.</p>`;
        return;
    }

    searchResults.style.display = 'block';
    searchResults.innerHTML = `<p>Loading...</p>`;

    try {
        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer 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` // OpenRouter API Key
            },
            body: JSON.stringify({
                model: "gpt-3.5-turbo", // Specify the model you want to use
                messages: [{ role: "user", content: query }],
                max_tokens: 150
            })
        });

        const data = await response.json();

        if (data.choices && data.choices.length > 0) {
            searchResults.innerHTML = `<p>${data.choices[0].message.content.trim()}</p>`;
        } else {
            searchResults.innerHTML = `<p>Sorry, I couldn't find an answer.</p>`;
        }
    } catch (error) {
        console.error(error);
        searchResults.innerHTML = `<p>An error occurred. Please try again later.</p>`;
    }
}

// Event Listener for ChatGPT Search
if (searchButton) {
    searchButton.addEventListener('click', handleSearch);
}
