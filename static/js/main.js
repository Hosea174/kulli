// Add hover effects to details buttons
document.querySelectorAll('.details-btn').forEach(button => {
  button.addEventListener('mouseenter', () => {
    button.style.transform = 'translateY(-2px)';
    button.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.2)';
  });
  
  button.addEventListener('mouseleave', () => {
    button.style.transform = 'translateY(0)';
    button.style.boxShadow = 'none';
  });
});

// Add click animation to details buttons
document.querySelectorAll('.details-btn').forEach(button => {
  button.addEventListener('click', () => {
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
      button.style.transform = 'scale(1)';
    }, 100);
  });
});

// Enhanced form validation for trip updates
document.querySelectorAll('.trip-update-form').forEach(form => {
  form.addEventListener('submit', function(e) {
    const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        field.classList.add('error');
        isValid = false;
      } else {
        field.classList.remove('error');
      }
    });

    if (!isValid) {
      e.preventDefault();
      showFlashMessage('Please fill all required fields', 'error');
    }
  });
});

// Add error styling for invalid fields
const errorStyle = document.createElement('style');
errorStyle.innerHTML = `
  .error {
    border-color: #dc2626 !important;
    background-color: #fee2e2 !important;
  }
  .error:focus {
    outline-color: #dc2626 !important;
  }
`;
document.head.appendChild(errorStyle);
