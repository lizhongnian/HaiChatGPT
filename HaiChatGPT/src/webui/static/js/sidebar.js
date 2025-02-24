
// 获取DOM元素
const loginButton = document.getElementById('login-button');
const logoutButton = document.getElementById('logout-button');
const usernameLabel = document.getElementById('username-label');
const public_user_alert = document.getElementById('public-user-alert');

user_name = localStorage.getItem('username')
// console.log(user_name); 

// 根据LocalStorage中的值显示是否登录
function show_login_by_local_storage() {
  local_user = localStorage.getItem('username');
  if (local_user == 'public' || local_user == null || local_user == 'null') {
    loginButton.style.display = 'inline-block';
    logoutButton.style.display = 'none';
    usernameLabel.style.display = 'inline-block';
    usernameLabel.innerText = 'public';
    public_user_alert.style.display = 'flex';
  // } else if () {
  //   // 未登录
  //   loginButton.style.display = 'inline-block';
  //   logoutButton.style.display = 'none';
  //   usernameLabel.style.display = 'none';
  //   usernameLabel.innerText = '';
  } else {
    // 已登录
    // console.log('sidebar.js 已登录', local_user);
    usernameLabel.innerText = localStorage.getItem('username');
    loginButton.style.display = 'none';
    logoutButton.style.display = 'inline-block';
    usernameLabel.style.display = 'inline-block';
    public_user_alert.style.display = 'none';
  }
}

show_login_by_local_storage();

// 点击登录按钮 显示登录对话框
loginButton.addEventListener('click', () => {
    window.location.href = 'login-dialog.html';
  });

// 点击用户名 显示用户信息
usernameLabel.addEventListener('click', () => {
    window.location.href = 'user-info.html';
  });

// 监听 登出按钮 清除本地存储的用户名
logoutButton.addEventListener('click', function(event) {
  // 阻止
  event.preventDefault();

  username = localStorage.getItem('username');
  // localStorage.removeItem('username'); 
  
  fetch('/logout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: username
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // 登出成功
      alert(data.message);
      // 清除本地存储的用户名
      // localStorage.setItem('username', null);
      localStorage.removeItem('username');
      // localStorage.removeItem('username');
      // 清除本地Cookie
      // document.cookie = 'session=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
      loginButton.style.display = 'inline-block';
      logoutButton.style.display = 'none';
      usernameLabel.style.display = 'none';
      usernameLabel.innerText = '';

      if (data.redirect){
        window.location.href = data.url;
      }

    } else {
      // 登出失败
      alert(data.message);
    }
  })
  .catch(error => {
    console.error(error);
    console.log('error');
  });

  // window.location.href = '/';
});








