// 前端交互
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏游戏时长输入框
    var habitSelect = document.getElementById('habitSelect');
    if (habitSelect) {
        var durInput = document.getElementById('durationInput');
        function toggleDuration() {
            durInput.style.display = habitSelect.value === '游戏' ? 'block' : 'none';
        }
        habitSelect.addEventListener('change', toggleDuration);
        toggleDuration();
    }

    // 财务页面 tab 切换
    window.showTab = function(name) {
        document.querySelectorAll('.tab-content').forEach(function(el) { el.classList.remove('active'); });
        document.querySelectorAll('.tab-btn').forEach(function(el) { el.classList.remove('active'); });
        var tab = document.getElementById('tab-' + name);
        if (tab) tab.classList.add('active');
        if (event && event.target) event.target.classList.add('active');
    };
});
