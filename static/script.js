document.addEventListener('DOMContentLoaded', () => {
  let timeout; // Timeout reference
  let isFetching = false; // Prevent overlapping requests

  // Function to adjust textarea height
  function adjustTextareaHeight(textarea) {
    textarea.style.height = '42px'; // Reset to initial height
    const scrollHeight = textarea.scrollHeight;
    if (scrollHeight > 42) {
      textarea.style.height = scrollHeight + 'px';
    }
  }

  function formatResponseText(text) {
  
    // Remove lines like "---"
    text = text.replace(/---+/g, "");
    
    // Handle citations section specially
    if (text.includes("**Citations**")) {
      // Split the text at "**Citations**"
      const parts = text.split("**Citations**");
      const mainContent = parts[0];
      let citationContent = parts[1];
  
      // Format each citation entry's URL into a link
      citationContent = citationContent.replace(
          /(available at )(https?:\/\/[^\s\n]+)/g,
          (match, prefix, url) => `${prefix}<a href="${url}" target="_blank" rel="noopener noreferrer" class="citation-link">${url}</a>`
      );
  
      // Wrap each citation in a <p> tag for block-level formatting
      citationContent = citationContent.replace(/\[(\d+)\]/g, '<p>[$1]');
  
      // Ensure the last citation is closed properly
      if (!citationContent.endsWith('</p>')) {
        citationContent += '</p>';
      }
  
      // Combine the parts back together with proper HTML structure
      text = mainContent + 
      '<div class="citations-section">' +
      '<strong class="section-heading">Citations</strong>' +
      citationContent +
      '</div>';
    }
  
    // Replace Markdown-like syntax for section headings
    text = text.replace(/\*\*(.*?)\*\*/g, "<strong class='section-heading'>$1</strong>"); // Section headings
  
    // Handle italics (single asterisks)
    text = text.replace(/\*((?!\*)[^*]+)\*/g, "<em>$1</em>");
  
    // Format list items and wrap in a single <ul>
    text = text.replace(/(?:^|\n)-\s*(.*?)(?=\n|$)/g, "<li>$1</li>");
    text = text.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/g, "<ul>$1</ul>"); // All lists
  
    // Replace double newlines with paragraph breaks
    text = text.replace(/\n\n/g, "</p><p>");
  
    // Wrap non-list content in <p> tags
    text = text.replace(/<\/ul>\s*<p>/g, "</ul>"); // Ensure lists are not wrapped in paragraphs
    text = `<p>${text}</p>`;
  
    return text;
  }

  function fadeInEffect(element, formattedText, duration = 1000) {
    element.style.opacity = '0';
    element.innerHTML = formattedText;

    // Trigger reflow
    element.offsetHeight;

    element.style.transition = `opacity ${duration}ms ease-in-out`;
    element.style.opacity = '1';
  }

  function fadeOutEffect(element, duration = 500) {
    element.style.transition = `opacity ${duration}ms ease-in-out`;
    element.style.opacity = '0';
    setTimeout(() => {
      element.style.display = 'none';
    }, duration);
  }

  function handleResponseText(element, text) {
    const formattedText = formatResponseText(text);

    // Support message with gradient glow effect
    const supportMessage = `
      <div class="support-message">
        <a href="https://www.buymeacoffee.com/nunnai" target="_blank">
          <img src="/public/images/coffee-full-logo.png" alt="Buy Me A Coffee">
        </a>
      </div>
    `;

    // Combine the formatted text with the support message
    const combinedContent = formattedText + supportMessage;

    fadeInEffect(element, combinedContent);
  }

  // Function to handle the search request
  async function handleSearch() {
    const questionInput = document.getElementById("question").value.trim();
    const responseDiv = document.getElementById("response");
    const searchButton = document.getElementById("askButton");
    const loadingAnimation = document.querySelector('.loading-animation');

    if (isFetching) {
      console.log("Request already in progress.");
      return;
    }

    if (!questionInput) {
      responseDiv.innerHTML = "<span class='error'>Please enter a question.</span>";
      return;
    }

    isFetching = true;
    searchButton.disabled = true;
    searchButton.innerHTML = "<i class='fas fa-spinner fa-spin'></i> Searching...";
    responseDiv.innerHTML = "";

    if (loadingAnimation) {
      loadingAnimation.classList.add('show');
    } else {
      console.warn("Loading animation element not found.");
    }

    try {
      if (timeout) clearTimeout(timeout);

      const controller = new AbortController();
      timeout = setTimeout(() => {
        controller.abort();
        console.log("Request timed out.");
      }, 60000);

      console.log("Sending fetch request...");
      const response = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: questionInput }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      handleResponseText(responseDiv, data.response);
    } catch (err) {
      console.error("Error during fetch:", err);
      responseDiv.innerHTML = `<span class='error'>${err.name === 'AbortError' ? "Request timed out. Please try again." : "An error occurred. Please try again later."}</span>`;
    } finally {
      isFetching = false;
      searchButton.disabled = false;
      searchButton.innerHTML = "<i class='fas fa-search'></i> Search";

      if (loadingAnimation) {
        loadingAnimation.classList.remove('show');
      }
    }
  }

  // Set up textarea auto-resize
  const searchInput = document.getElementById("question");
  searchInput.addEventListener('input', () => adjustTextareaHeight(searchInput));

  // Initial height adjustment
  adjustTextareaHeight(searchInput);

  // Attach event listeners
  document.getElementById("askButton").addEventListener("click", handleSearch);

  // Modified keypress handler for textarea
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  });

  // Add scroll detection for response box fade effect
  document.getElementById("response").addEventListener("scroll", function() {
    const element = this;
    const isAtBottom = Math.abs((element.scrollHeight - element.scrollTop) - element.clientHeight) < 1;

    if (isAtBottom) {
      element.classList.add('at-bottom');
    } else {
      element.classList.remove('at-bottom');
    }
  });
});
