import { useState } from 'react';
import api from '../api';

function Login() {
    const [email, setEmail] = useState('test@example.com');
    const [password, setPassword] = useState('123456');
    const [error, setError] = useState(null);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(null);

        try {
            const response = await api.post('/api/login', { email, password });
            if (response.data.status === 'success') {
                // ВАЖНО: Если авторизация успешна, мы говорим браузеру закрыть этот попап!
                IdentityProvider.close();
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Ошибка авторизации");
        }
    };

    return (
        <div style={styles.container}>
            <h2>Вход в SSO (IdP)</h2>
            <form onSubmit={handleLogin} style={styles.form}>
                <input 
                    type="email" 
                    value={email} 
                    onChange={e => setEmail(e.target.value)} 
                    placeholder="Email" 
                    style={styles.input} 
                    required 
                />
                <input 
                    type="password" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    placeholder="Пароль" 
                    style={styles.input} 
                    required 
                />
                <button type="submit" style={styles.btn}>Войти</button>
            </form>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
}

const styles = {
    container: { fontFamily: 'Arial', textAlign: 'center', padding: '20px' },
    form: { display: 'flex', flexDirection: 'column', gap: '15px', maxWidth: '300px', margin: '0 auto' },
    input: { padding: '10px', fontSize: '16px', border: '1px solid #ccc', borderRadius: '4px' },
    btn: { background: '#28a745', color: 'white', padding: '10px', border: 'none', borderRadius: '4px', fontSize: '16px', cursor: 'pointer' }
};

export default Login;