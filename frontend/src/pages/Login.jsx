// frontend/src/pages/Login.jsx
import { useState } from 'react';
import api from '../api';

function Login() {
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState('test@example.com');
    const [password, setPassword] = useState('123456');
    const [name, setName] = useState('Фёдор');
    
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setMessage(null);
        setIsLoading(true);

        try {
            if (isRegister) {
                await api.post('/api/register', { name, email, password });
                setMessage("✅ Регистрация успешна! Теперь вы можете войти.");
                setIsRegister(false);
            } else {
                const response = await api.post('/api/login', { email, password });
                if (response.data.status === 'success') {
                    setMessage("✅ Успешно! Синхронизация с браузером...");
                    
                    setTimeout(() => {
                        // Идем на трамплин бэкенда, который выставит куки и перенаправит обратно в React
                        // Кодируем адрес нашей главной страницы React
                        const returnUrl = encodeURIComponent("https://rp.test:5173/");
                        
                        // Переходим на idp.test, чтобы Chrome легально записал статус
                        window.location.href = `https://idp.test/mark-login?redirect_url=${returnUrl}`;
                    }, 1000);
                }
            }
        } catch (err) {
            setError("❌ " + (err.response?.data?.detail || "Ошибка соединения"));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2>{isRegister ? "Создать аккаунт" : "Вход в SSO"}</h2>
                
                {error && <div style={styles.errorBox}>{error}</div>}
                {message && <div style={styles.successBox}>{message}</div>}

                <form onSubmit={handleSubmit} style={styles.form}>
                    {isRegister && (
                        <input type="text" placeholder="Ваше имя" value={name} onChange={e => setName(e.target.value)} style={styles.input} required />
                    )}
                    <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={styles.input} required />
                    <input type="password" placeholder="Пароль" value={password} onChange={e => setPassword(e.target.value)} style={styles.input} required />
                    <button type="submit" style={styles.btn} disabled={isLoading}>
                        {isLoading ? "Загрузка..." : (isRegister ? "Зарегистрироваться" : "Войти")}
                    </button>
                </form>

                <button onClick={() => { setIsRegister(!isRegister); setError(null); setMessage(null); }} style={styles.linkBtn}>
                    {isRegister ? "Уже есть аккаунт? Войти" : "Нет аккаунта? Регистрация"}
                </button>
            </div>
        </div>
    );
}

const styles = {
    container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5', fontFamily: 'Arial' },
    card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.1)', width: '350px', textAlign: 'center' },
    form: { display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' },
    input: { padding: '12px', borderRadius: '8px', border: '1px solid #ccc', fontSize: '15px' },
    btn: { background: '#007bff', color: 'white', border: 'none', padding: '14px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' },
    linkBtn: { background: 'none', border: 'none', color: '#007bff', marginTop: '20px', cursor: 'pointer', fontSize: '14px' },
    errorBox: { background: '#f8d7da', color: '#721c24', padding: '12px', borderRadius: '8px', fontSize: '14px', marginTop: '15px' },
    successBox: { background: '#d4edda', color: '#155724', padding: '12px', borderRadius: '8px', fontSize: '14px', marginTop: '15px' }
};

export default Login;