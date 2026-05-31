document.addEventListener('DOMContentLoaded', () => {


const themeToggle =
    document.getElementById('theme-toggle');

const currentTheme =
    localStorage.getItem('theme') || 'light';

document.documentElement.setAttribute(
    'data-theme',
    currentTheme
);

if(themeToggle){

    themeToggle.checked =
        currentTheme === 'dark';

    themeToggle.addEventListener(
        'change',
        (e) => {

            const theme =
                e.target.checked
                ? 'dark'
                : 'light';

            document.documentElement.setAttribute(
                'data-theme',
                theme
            );

            localStorage.setItem(
                'theme',
                theme
            );
        }
    );
}

const submissionType =
    document.getElementById('submission_type');

const textFields =
    document.getElementById('text-fields');

const headline =
    document.getElementById('headline');

const url =
    document.getElementById('url');

const content =
    document.getElementById('content');

function toggleFields(){

    if(!submissionType) return;

    if(submissionType.value === 'image'){

        textFields.style.display = 'none';

        headline.removeAttribute('required');
        url.removeAttribute('required');
        content.removeAttribute('required');

    }
    else{

        textFields.style.display = 'block';

        headline.setAttribute('required', true);
        url.setAttribute('required', true);
        content.setAttribute('required', true);
    }
}

if(submissionType){

    submissionType.addEventListener(
        'change',
        toggleFields
    );

    toggleFields();
}

});
