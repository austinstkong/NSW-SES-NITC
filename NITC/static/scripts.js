// Global variables
let registrationNumber = ''; // Store the registration number
let selectedTagIds = [];    // Store selected tag IDs
let debounceTimer;          // For debouncing the API call

// Function to load data by Tag Group ID
function loadDataByTagGroupId(tagGroupId) {
    fetch(`/get_items_by_taggroupid?tagGroupId=${tagGroupId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const dropdown = document.getElementById('dropdownList');
            dropdown.innerHTML = ''; // Clear existing options

            // Populate the dropdown with options based on the response
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item.tagId; 
                option.textContent = item.Name;
                dropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
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

// Function to gather selected tag IDs from both icons and dropdowns
function gatherSelectedTagIds() {
    const combinedTagIds = [...selectedTagIds]; // IDs from icon selections

    // Add IDs from the dropdown selection(s)
    const dropdown = document.getElementById('dropdownList');
    if (dropdown && dropdown.value) {
        combinedTagIds.push(dropdown.value);
    }

    return combinedTagIds;
}


// Update registration field
function updateRegistrationField() {
    const registrationInput = document.getElementById('registrationNumber');
    if (registrationInput) {
        registrationInput.value = registrationNumber;
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

// Hide error message
function hideError() {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Function to clear registration number and search results
function clearNumber() {
    console.log("Clearing number and search results");  // Debugging log
    registrationNumber = '';
    updateRegistrationField();

    // Assuming 'memberSearchResults' and 'taggroup' are IDs of the elements to clear
    clearDropdown(document.getElementById('memberSearchResults'));
    clearDropdown(document.getElementById('dropdownList'));  // Update this with correct ID

    resetIcons();
}


// Debounce function for API calls
function debounce(func, wait) {
    return function executedFunction(...args) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            func(...args);
        }, wait);
    };
}

// Function to check if the member is already checked in
function checkMemberCheckInStatus(registrationNumber, callback) {
    fetch(`/check_in_status?registrationNumber=${registrationNumber}`)
        .then(response => response.json())
        .then(data => {
            callback(data.isCheckedIn);
        })
        .catch(error => {
            showError(`Error checking check-in status: ${error}`);
        });
}

// Function to handle check-in and check-out
function handleCheck(action) {
    if (!registrationNumber.startsWith('400')) {
        showError('Registration number must start with 400.');
        return;
    }

    // Check-in logic
    if (action === 'check_in') {
        checkMemberCheckInStatus(registrationNumber, (isCheckedIn) => {
            if (isCheckedIn) {
                showError('Member is already checked in.');
            } else {
                performCheckInOrOut(action);
            }
        });
    } else {
        performCheckInOrOut(action);
    }
}

// Function to perform the actual check-in or check-out
function performCheckInOrOut(action) {
    const allSelectedTagIds = gatherSelectedTagIds();
    const formData = new URLSearchParams({
        'registrationNumber': registrationNumber,
        'TagIds': JSON.stringify(allSelectedTagIds)
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
            clearNumber(); // Clears the input and other fields
            hideError();   // Clears any existing error messages
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

// Fetch members from the API and check their check-in status
function searchMember(registrationNumber) {
    const searchUrl = `/search_member?registrationNumber=${registrationNumber}`;
    fetch(searchUrl)
        .then(response => response.ok ? response.json() : Promise.reject(`HTTP error! Status: ${response.status}`))
        .then(data => {
            populateDropdown(data.Results || [], 'memberSearchResults', 'No members found with this number.');

            // If members are found, check their check-in status
            if (data.Results && data.Results.length > 0) {
                checkMemberCheckInStatus(registrationNumber, (isCheckedIn) => {
                    if (isCheckedIn) {
                        showError('Member is already checked in.');
                    } else {
                        hideError();
                    }
                });
            }
        })
        .catch(error => {
            showError("Fetch error: " + error.message);
            console.error("Fetch error:", error.message);
        });
}

// Function to initialize the script and set up event listeners
function init() {
    document.querySelectorAll('.tag-icon').forEach(icon => {
        icon.addEventListener('click', toggleIconSelection);
    });

    // Additional event listener attachments (e.g., for registrationInput, buttons)
}

// Attach the init function to the DOMContentLoaded event
// document.addEventListener('DOMContentLoaded', init);

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

// Function to clear a dropdown helper function
function clearDropdown(element) {
    if (element) {
        element.innerHTML = '';
    }
}

// Function to reset icons to default state
function resetIcons() {
    selectedTagIds = [];
    document.querySelectorAll('.tag-icon').forEach(icon => {
        icon.style.opacity = '1';
    });
}

// Function to initialize the script and set up event listeners
function init() {
    document.querySelectorAll('.tag-icon').forEach(icon => {
        icon.addEventListener('click', toggleIconSelection);
    });

    // Attach event listeners for keypad buttons
    document.querySelectorAll('.keypad-container .key[data-number]').forEach(button => {
        button.addEventListener('click', () => appendNumber(button.getAttribute('data-number')));
    });

    // Event listeners for various buttons and inputs
    document.getElementById('clearNumber')?.addEventListener('click', clearNumber);
    document.getElementById('backspace')?.addEventListener('click', () => {
        registrationNumber = registrationNumber.slice(0, -1);
        updateRegistrationField();
    });
    document.getElementById('checkInButton')?.addEventListener('click', () => handleCheck('check_in'));
    document.getElementById('checkOutButton')?.addEventListener('click', () => handleCheck('check_out'));

    const registrationInput = document.getElementById('registrationNumber');
    if (registrationInput) {
        registrationInput.addEventListener('input', function() {
            registrationNumber = this.value;
            updateRegistrationField();
            if (registrationNumber.length >= 7) {
                debounce(searchMember, 500)(registrationNumber);
            }
        });
        registrationInput.focus();
    }
}

// Attach the init function to the DOMContentLoaded event
document.addEventListener('DOMContentLoaded', init);