(function(){'use strict';
var root=document.documentElement,t=document.getElementById('themeToggle');
function theme(x){if(x==='dark')root.setAttribute('data-theme','dark');else root.removeAttribute('data-theme');t.textContent=x==='dark'?'Light mode':'Dark mode';t.setAttribute('aria-pressed',x==='dark'?'true':'false');}
var s=null;try{s=localStorage.getItem('arc-ce-theme');}catch(e){}
theme(s||(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
t.addEventListener('click',function(){var n=root.getAttribute('data-theme')==='dark'?'light':'dark';theme(n);try{localStorage.setItem('arc-ce-theme',n);}catch(e){}});
var secs=Array.prototype.slice.call(document.querySelectorAll('main section[id]')),links={};document.querySelectorAll('.rail a').forEach(function(a){links[a.getAttribute('data-k')]=a;});
function spy(){var cur=null;secs.forEach(function(s){if(s.getBoundingClientRect().top<=120)cur=s.id;});Object.keys(links).forEach(function(k){links[k].classList.toggle('is-on',k===cur);});}
var tick=false;window.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(function(){spy();tick=false;});}},{passive:true});spy();
})();
