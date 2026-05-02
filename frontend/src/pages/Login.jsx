import { useState } from 'react';
import api from '../api';

function Login() {
    const[isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState('test@example.com');
    const [password, setPassword] = useState('123456');
    const[name, setName] = useState('Фёдор'); 
    
    const[message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const[isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setMessage(null);
        setIsLoading(true);

        try {
            if (isRegister) {
                // ЛОГИКА РЕГИСТРАЦИИ
                await api.post('/api/register', { name, email, password });
                setMessage("✅ Регистрация успешна! Теперь вы можете войти.");
                setIsRegister(false); // Автоматически переключаем на форму входа
            } else {
                // ЛОГИКА ВХОДА
                const response = await api.post('/api/login', { email, password });
                if (response.data.status === 'success') {
                    setMessage("✅ Вы успешно вошли! Перенаправляем...");
                    
                    setTimeout(() => {
                        // Если мы открыты как попап FedCM, браузер закроет окно
                        if (window.IdentityProvider) {
                            try { window.IdentityProvider.close(); } catch(e) {}
                        }
                        // Если мы в обычной вкладке (или close не сработал), переходим на главную
                        window.location.href = "/";
                    }, 1500);
                }
            }
        } catch (err) {
            setError("❌ " + (err.response?.data?.detail || "Произошла ошибка соединения"));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h2>{isRegister ? "Создать аккаунт" : "Вход в SSO"}</h2>
                
                {/* Блоки уведомлений */}
                {error && <div style={styles.errorBox}>{error}</div>}
                {message && <div style={styles.successBox}>{message}</div>}

                <form onSubmit={handleSubmit} style={styles.form}>
                    {isRegister && (
                        <input 
                            type="text" 
                            placeholder="Ваше имя" 
                            value={name} 
                            onChange={e => setName(e.target.value)} 
                            style={styles.input} required 
                        />
                    )}
                    <input 
                        type="email" 
                        placeholder="Email" 
                        value={email} 
                        onChange={e => setEmail(e.target.value)} 
                        style={styles.input} required 
                    />
                    <input 
                        type="password" 
                        placeholder="Пароль" 
                        value={password} 
                        onChange={e => setPassword(e.target.value)} 
                        style={styles.input} required 
                    />
                    <button type="submit" style={styles.btn} disabled={isLoading}>
                        {isLoading ? "Загрузка..." : (isRegister ? "Зарегистрироваться" : "Войти")}
                    </button>
                </form>

                <button 
                    onClick={() => {
                        setIsRegister(!isRegister);
                        setError(null);
                        setMessage(null);
                    }} 
                    style={styles.linkBtn}
                >
                    {isRegister ? "Уже есть аккаунт? Войти" : "Нет аккаунта? Регистрация"}
                </button>
            </div>
        </div>
    );
}

const styles = {
    container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5', fontFamily: 'Arial' },
    card: { background: 'white', padding: '30px', borderRadius: '12px', boxShadow: '0 4px 10px rgba(0,0,0,0.1)', width: '320px', textAlign: 'center' },
    form: { display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '15px' },
    input: { padding: '12px', borderRadius: '6px', border: '1px solid #ccc', fontSize: '15px' },
    btn: { background: '#007bff', color: 'white', border: 'none', padding: '12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' },
    linkBtn: { background: 'none', border: 'none', color: '#007bff', marginTop: '15px', cursor: 'pointer', fontSize: '14px' },
    errorBox: { background: '#f8d7da', color: '#721c24', padding: '10px', borderRadius: '6px', fontSize: '14px', marginTop: '10px' },
    successBox: { background: '#d4edda', color: '#155724', padding: '10px', borderRadius: '6px', fontSize: '14px', marginTop: '10px' }
};

export default Login;