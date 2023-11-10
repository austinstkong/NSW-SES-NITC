document.addEventListener('DOMContentLoaded', function() {
  let registrationNumber = ''; // Store the registration number
  let selectedTagIds = [];    // Store selected tag IDs
  let debounceTimer;          // For debouncing the API call

  // Get DOM elements once and reuse
  const registrationInput = document.getElementById('registrationNumber');
  const memberSearchResults = document.getElementById('memberSearchResults');
  const lastNameSearchResults = document.getElementById('lastNameSearchResults');
  const errorDiv = document.getElementById('error-message'); // Ensure you have this element in your HTML

  // Common update function for registration field and error handling
  function updateRegistrationField() {
      if (registrationInput) {
          registrationInput.value = registrationNumber;
      }
      
      if (registrationNumber.length >= 7 && !registrationNumber.startsWith('400')) {
          showError("Please enter a valid member number.");
      } else {
          hideError();
      }
  }

  function backspace() {
    // Remove the last character from registrationNumber
    registrationNumber = registrationNumber.slice(0, -1);
    // Update the registration field to reflect the change
    updateRegistrationField();
        }

  // Display error messages
  function showError(message) {
      if (errorDiv) {
          errorDiv.textContent = message;
          errorDiv.style.display = 'block';
      }
  }

  // Hide error messages
  function hideError() {
      if (errorDiv) {
          errorDiv.style.display = 'none';
      }
  }

  // Clear registration number and search results
  function clearNumber() {
      registrationNumber = '';
      updateRegistrationField();
      clearDropdown(memberSearchResults);
      clearDropdown(lastNameSearchResults);
      resetIcons();
  }

  // Clear dropdown helper function
  function clearDropdown(element) {
      if (element) {
          element.innerHTML = '';
      }
  }

  // Reset icons to default state
  function resetIcons() {
      selectedTagIds = [];
      document.querySelectorAll('.tag-icon').forEach(icon => {
          icon.style.opacity = '1';
      });
  }

  // Debounce function for API calls
  function debounce(func, wait) {
      return function executedFunction(...args) {
          const later = function() {
              clearTimeout(debounceTimer);
              func(...args);
          };
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(later, wait);
      };
  }

  // Function to handle check-in and check-out
  function handleCheck(action) {
      // Check for activity selection on check-out
    if (action === 'check_out' && selectedTagIds.length === 0) {
        showError('Please select at least one activity before checking out.');
        return; // Exit the function if validation fails
    }

    if (!registrationNumber.startsWith('400')) {
        showError('Registration number must start with 400.');
        return; // Exit the function if validation fails
    }
    
    const formData = new URLSearchParams({
        'registrationNumber': registrationNumber,
        'TagIds': JSON.stringify(selectedTagIds)
    });
    
    fetch(`/${action}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData.toString()
    })
    .then(response => response.ok ? response.json() : Promise.reject(`Failed to ${action}. HTTP Status: ${response.status}`))
    .then(data => {
        if (data.status === 'success') {
            clearNumber();
            alert(`Checked ${action === 'check_in' ? 'in' : 'out'} successfully.`);
        } else {
            showError(`Failed to ${action}. ${data.message}`);
        }
    })
    .catch(error => {
        showError(`An error occurred while trying to ${action}. Please try again.`);
        console.error(`Error during ${action}:`, error);
    });
}
  // Function to append a number to the registrationNumber
  function appendNumber(num) {
      registrationNumber += num;
      updateRegistrationField();
      if (registrationNumber.length >= 7 && registrationNumber.startsWith('400')) {
          debounce(searchMember, 500)(registrationNumber);
      }
  }

  // Fetch members from the API
  function searchMember(registrationNumber) {
      const searchUrl = `/search_member?registrationNumber=${registrationNumber}`;
      fetch(searchUrl)
          .then(response => response.ok ? response.json() : Promise.reject(`HTTP error! Status: ${response.status}`))
          .then(data => populateDropdown(data.Results || [], 'memberSearchResults', 'No members found with this number.'))
          .catch(error => {
              showError("Fetch error: " + error.message);
              console.error("Fetch error:", error.message);
          });
  }

  // Populate the dropdown with search results
  function populateDropdown(results, elementId, errorPrompt) {
      clearDropdown(memberSearchResults);
      clearDropdown(lastNameSearchResults);

      if (Array.isArray(results) && results.length > 0) {
          const dropdown = document.createElement('select');
          dropdown.id = `${elementId}_dropdown`;
          
          results.forEach(member => {
              const option = document.createElement('option');
              option.value = member.Id;
              option.text = `${member.FirstName} ${member.LastName} (${member.EntityName})`;
              dropdown.appendChild(option);
          });
          memberSearchResults.appendChild(dropdown);
      } else {
          memberSearchResults.innerHTML = errorPrompt;
      }
  }

  // Toggle icon selection
  function toggleIconSelection(event) {
      const iconElement = event.currentTarget;
      const tagId = iconElement.getAttribute('data-tagid');
      const index = selectedTagIds.indexOf(tagId);
      if (index > -1) {
          selectedTagIds.splice(index, 1);
          iconElement.style.opacity = '1';
      } else {
          selectedTagIds.push(tagId);
          iconElement.style.opacity = '0.5';
      }
  }

  // Attach event listeners
  document.querySelectorAll('.keypad-container .key[data-number]').forEach(button => {
      button.addEventListener('click', () => appendNumber(button.getAttribute('data-number')));
  });
  
  if (registrationInput) {
      registrationInput.addEventListener('input', function() {
          registrationNumber = this.value;
          updateRegistrationField();
          if (registrationNumber.length >= 7) {
              debounce(searchMember, 500)(registrationNumber);
          }
      });
  }
  
  document.getElementById('clearNumber')?.addEventListener('click', clearNumber);
  document.getElementById('backspace').addEventListener('click', backspace);

  document.getElementById('checkInButton')?.addEventListener('click', () => handleCheck('check_in'));
  document.getElementById('checkOutButton')?.addEventListener('click', () => handleCheck('check_out'));

  document.querySelectorAll('.tag-icon').forEach(icon => {
      icon.addEventListener('click', toggleIconSelection);
  });
});
