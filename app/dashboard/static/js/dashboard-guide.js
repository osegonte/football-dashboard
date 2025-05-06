/**
 * Football Dashboard - Guides and Help System
 * Provides interactive guides, tooltips, and help features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize guide panels
    initGuides();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize pipeline status indicators
    initPipelineStatus();
    
    // Optional: Initialize onboarding tour for first-time visitors
    if (isFirstTimeVisitor()) {
        initOnboardingTour();
    }
});

/**
 * Initialize expandable guide panels
 */
function initGuides() {
    const guidePanels = document.querySelectorAll('.guide-panel');
    
    guidePanels.forEach(panel => {
        const toggle = panel.querySelector('.guide-toggle');
        const content = panel.querySelector('.guide-content');
        const icon = toggle.querySelector('i.fa-chevron-down, i.fa-chevron-up');
        
        // Set initial state
        if (toggle && content) {
            toggle.addEventListener('click', () => {
                content.classList.toggle('active');
                
                // Toggle icon if present
                if (icon) {
                    if (content.classList.contains('active')) {
                        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
                    } else {
                        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
                    }
                }
            });
        }
    });
}

/**
 * Initialize help tooltips
 */
function initTooltips() {
    // Find all elements with data-tooltip attribute
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        const tooltipText = element.getAttribute('data-tooltip');
        
        // Using Bootstrap's tooltip if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            new bootstrap.Tooltip(element, {
                title: tooltipText,
                placement: 'top',
                trigger: 'hover'
            });
        } else {
            // Fallback for when Bootstrap JS is not available
            element.title = tooltipText;
        }
    });
}

/**
 * Initialize pipeline status indicators
 */
function initPipelineStatus() {
    const pipelineStatus = document.getElementById('pipeline-status');
    
    if (!pipelineStatus) return;
    
    // Monitor status and update appropriate classes
    function updatePipelineStatus(status) {
        // Remove all status classes
        pipelineStatus.classList.remove(
            'pipeline-idle',
            'pipeline-running',
            'pipeline-success',
            'pipeline-error'
        );
        
        // Add the appropriate class based on status
        pipelineStatus.classList.add(`pipeline-${status}`);
        
        // Update icon if present
        const statusIcon = pipelineStatus.querySelector('i');
        if (statusIcon) {
            statusIcon.className = ''; // Clear existing classes
            statusIcon.classList.add('fas');
            
            // Add appropriate icon class
            switch(status) {
                case 'running':
                    statusIcon.classList.add('fa-sync-alt', 'fa-spin');
                    break;
                case 'success':
                    statusIcon.classList.add('fa-check-circle');
                    break;
                case 'error':
                    statusIcon.classList.add('fa-exclamation-circle');
                    break;
                default:
                    statusIcon.classList.add('fa-info-circle');
            }
        }
    }
    
    // Check if we have pipeline status data from the server
    if (pipelineStatus.dataset.status) {
        updatePipelineStatus(pipelineStatus.dataset.status);
    }
    
    // If there's a pipeline form, update status on submit
    const pipelineForm = document.querySelector('form[action*="run_pipeline"]');
    if (pipelineForm) {
        pipelineForm.addEventListener('submit', function(e) {
            updatePipelineStatus('running');
        });
    }
}

/**
 * Check if this is the user's first visit
 */
function isFirstTimeVisitor() {
    if (!localStorage.getItem('football_dashboard_visited')) {
        localStorage.setItem('football_dashboard_visited', 'true');
        return true;
    }
    return false;
}

/**
 * Initialize onboarding tour for first-time visitors
 */
function initOnboardingTour() {
    // Create welcome modal
    const welcomeModal = document.createElement('div');
    welcomeModal.className = 'modal fade';
    welcomeModal.id = 'welcomeModal';
    welcomeModal.setAttribute('tabindex', '-1');
    welcomeModal.setAttribute('aria-labelledby', 'welcomeModalLabel');
    welcomeModal.setAttribute('aria-hidden', 'true');
    
    welcomeModal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="welcomeModalLabel">Welcome to Football Dashboard</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Welcome to the Football Data Dashboard! This dashboard provides comprehensive information about football fixtures, teams, and leagues.</p>
                    <p>Here's what you can do:</p>
                    <ul>
                        <li><strong>View Fixtures</strong> - See upcoming football matches</li>
                        <li><strong>Explore Teams</strong> - Get detailed information about teams</li>
                        <li><strong>Browse Leagues</strong> - See league information and standings</li>
                        <li><strong>View Statistics</strong> - Explore football data visualizations</li>
                    </ul>
                    <p>Would you like a quick tour of the dashboard?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Skip Tour</button>
                    <button type="button" class="btn btn-primary" id="startTourBtn">Start Tour</button>
                </div>
            </div>
        </div>
    `;
    
    // Append modal to body
    document.body.appendChild(welcomeModal);
    
    // Show welcome modal
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const modal = new bootstrap.Modal(welcomeModal);
        modal.show();
        
        // Handle start tour button
        const startTourBtn = document.getElementById('startTourBtn');
        if (startTourBtn) {
            startTourBtn.addEventListener('click', function() {
                modal.hide();
                startGuidedTour();
            });
        }
    }
}

/**
 * Start guided tour of the dashboard
 */
function startGuidedTour() {
    // Define tour steps based on the current page
    const currentPath = window.location.pathname;
    let tourSteps = [];
    
    // Home page tour steps
    if (currentPath === '/' || currentPath.includes('index')) {
        tourSteps = [
            {
                element: '.navbar',
                title: 'Navigation',
                content: 'Use this menu to navigate between different sections of the dashboard.',
                position: 'bottom'
            },
            {
                element: '.dashboard-stat:first-child',
                title: 'Dashboard Statistics',
                content: 'These cards show key metrics about the football data.',
                position: 'top'
            },
            {
                element: '.card:has(.match-card)',
                title: 'Upcoming Matches',
                content: 'Here you can see upcoming football matches grouped by date.',
                position: 'left'
            },
            {
                element: 'form[action*="run_pipeline"]',
                title: 'Data Pipeline',
                content: 'Click this button to update the dashboard with the latest football data.',
                position: 'top'
            }
        ];
    }
    
    // Fixtures page tour steps
    else if (currentPath.includes('fixtures')) {
        tourSteps = [
            {
                element: '.card:has(select[name="days"])',
                title: 'Filter Fixtures',
                content: 'Use these filters to customize which matches are displayed.',
                position: 'top'
            },
            {
                element: 'table.table',
                title: 'Match Fixtures',
                content: 'This table shows all upcoming football matches based on your filters.',
                position: 'top'
            },
            {
                element: '.status-badge',
                title: 'Match Status',
                content: 'These badges indicate the current status of each match.',
                position: 'right'
            }
        ];
    }
    
    // Teams page tour steps
    else if (currentPath.includes('teams')) {
        tourSteps = [
            {
                element: '.card:has(select[name="league"])',
                title: 'Filter Teams',
                content: 'Use these filters to find teams from specific leagues.',
                position: 'top'
            },
            {
                element: '.list-group-item:first-child',
                title: 'Team List',
                content: 'Click on any team to view detailed information.',
                position: 'right'
            },
            {
                element: '.badge.bg-success',
                title: 'Data Coverage',
                content: 'Teams with this badge have additional detailed data available.',
                position: 'left'
            }
        ];
    }
    
    // Implement a simple tour using popovers
    // For a production implementation, consider using a library like intro.js or shepherd.js
    let currentStep = 0;
    
    function showStep(step) {
        if (step >= tourSteps.length) {
            endTour();
            return;
        }
        
        const tourStep = tourSteps[step];
        const element = document.querySelector(tourStep.element);
        
        if (!element) {
            // Skip to next step if element not found
            showStep(step + 1);
            return;
        }
        
        // Create popover element
        const popover = document.createElement('div');
        popover.className = 'tour-popover card';
        popover.style.position = 'absolute';
        popover.style.zIndex = '1060';
        popover.style.maxWidth = '300px';
        popover.style.boxShadow = '0 0 20px rgba(0,0,0,0.2)';
        
        popover.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${tourStep.title}</h5>
                <p class="card-text">${tourStep.content}</p>
                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="tourPrevBtn">Previous</button>
                    <span class="align-self-center">${step + 1} of ${tourSteps.length}</span>
                    <button type="button" class="btn btn-sm btn-primary" id="tourNextBtn">
                        ${step < tourSteps.length - 1 ? 'Next' : 'Finish'}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(popover);
        
        // Position the popover
        positionPopover(popover, element, tourStep.position);
        
        // Highlight the element
        const originalStyle = element.getAttribute('style') || '';
        element.style.position = 'relative';
        element.style.zIndex = '1050';
        element.style.boxShadow = '0 0 0 4px rgba(50, 130, 184, 0.5)';
        
        // Add event listeners to buttons
        document.getElementById('tourPrevBtn').addEventListener('click', function() {
            removePopover();
            showStep(step - 1 >= 0 ? step - 1 : 0);
        });
        
        document.getElementById('tourNextBtn').addEventListener('click', function() {
            removePopover();
            showStep(step + 1);
        });
        
        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        function removePopover() {
            if (popover.parentNode) {
                popover.parentNode.removeChild(popover);
            }
            element.setAttribute('style', originalStyle);
        }
    }
    
    function positionPopover(popover, element, position) {
        const elementRect = element.getBoundingClientRect();
        const popoverRect = popover.getBoundingClientRect();
        
        let top, left;
        
        switch(position) {
            case 'top':
                top = elementRect.top - popoverRect.height - 10 + window.scrollY;
                left = elementRect.left + (elementRect.width / 2) - (popoverRect.width / 2) + window.scrollX;
                break;
            case 'bottom':
                top = elementRect.bottom + 10 + window.scrollY;
                left = elementRect.left + (elementRect.width / 2) - (popoverRect.width / 2) + window.scrollX;
                break;
            case 'left':
                top = elementRect.top + (elementRect.height / 2) - (popoverRect.height / 2) + window.scrollY;
                left = elementRect.left - popoverRect.width - 10 + window.scrollX;
                break;
            case 'right':
                top = elementRect.top + (elementRect.height / 2) - (popoverRect.height / 2) + window.scrollY;
                left = elementRect.right + 10 + window.scrollX;
                break;
            default:
                top = elementRect.bottom + 10 + window.scrollY;
                left = elementRect.left + window.scrollX;
        }
        
        // Make sure popover stays within viewport
        if (left < 0) left = 10;
        if (left + popoverRect.width > window.innerWidth) left = window.innerWidth - popoverRect.width - 10;
        if (top < 0) top = 10;
        
        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
    }
    
    function endTour() {
        // Create completion modal
        const completionModal = document.createElement('div');
        completionModal.className = 'modal fade';
        completionModal.id = 'tourCompletionModal';
        completionModal.setAttribute('tabindex', '-1');
        completionModal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Tour Completed!</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>You've completed the tour of the Football Dashboard. Here's a summary of what you've learned:</p>
                        <ul>
                            <li>How to navigate between different sections</li>
                            <li>How to filter and view fixtures</li>
                            <li>How to explore team information</li>
                            <li>How to update data using the pipeline</li>
                        </ul>
                        <p>Feel free to explore the dashboard. If you need help, look for the <span class="help-tooltip">i</span> icons throughout the interface.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Start Exploring</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(completionModal);
        
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modal = new bootstrap.Modal(completionModal);
            modal.show();
            
            completionModal.addEventListener('hidden.bs.modal', function() {
                completionModal.parentNode.removeChild(completionModal);
            });
        }
    }
    
    // Start the tour with the first step
    if (tourSteps.length > 0) {
        showStep(0);
    } else {
        // If no tour steps for this page, just show a welcome toast
        showWelcomeToast();
    }
}

/**
 * Show a welcome toast notification
 */
function showWelcomeToast() {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-primary border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '1050';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                Welcome to the Football Dashboard! Explore and enjoy.
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', function() {
            toast.parentNode.removeChild(toast);
        });
    } else {
        // Fallback if Bootstrap JS is not available
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}