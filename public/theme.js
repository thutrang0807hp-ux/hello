/* Every page load starts light; theme switches stay within the current visit. */
(()=>{
 const root=document.documentElement;
 let dark=false;
 try{localStorage.removeItem('freelance-theme');}catch{}
 root.dataset.theme=dark?'dark':'light';
 const button=document.createElement('button');button.id='themeToggle';button.type='button';
 const sync=()=>{button.innerHTML='<span class=nav-icon aria-hidden=true>'+ (dark?'☀':'☾')+'</span><span class=nav-label>'+ (dark?'Chế độ sáng':'Chế độ tối')+'</span>';button.setAttribute('aria-label',dark?'Chuyển sang chế độ sáng':'Chuyển sang chế độ tối');button.setAttribute('aria-pressed',String(dark));};
 button.onclick=()=>{dark=!dark;root.dataset.theme=dark?'dark':'light';sync();};
 button.className='sidebar-theme-toggle';
 document.querySelector('#sidebarNav .sidebar-bottom').prepend(button);sync();
 window.addEventListener('pageshow',event=>{if(event.persisted){dark=false;root.dataset.theme='light';sync();}});
})();
