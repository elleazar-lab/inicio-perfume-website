-- ========== POSTGRESQL SCHEMA FOR RENDER DEPLOYMENT ==========

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    customer_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(30) UNIQUE,
    customer_name VARCHAR(100),
    customer_email VARCHAR(100),
    total_amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50) DEFAULT 'QRPH',
    payment_reference VARCHAR(100),
    payment_verified BOOLEAN DEFAULT FALSE,
    shipping_address TEXT,
    phone VARCHAR(20),
    order_note TEXT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    price DECIMAL(10,2)
);

-- Addresses table
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    label VARCHAR(50),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    street VARCHAR(255) NOT NULL,
    apartment VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password Resets table
CREATE TABLE IF NOT EXISTS password_resets (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    token VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample admin
INSERT INTO users (name, email, password, role, customer_id) 
VALUES ('Admin', 'admin@inicio.com', 'admin123', 'admin', 'ADMIN-000001')
ON CONFLICT (email) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock, image_url) VALUES
('LAST CALL', 'Similar to Lacoste Red. A fresh, energetic fragrance with citrus and woody notes.', 449, 50, 'last-call.png'),
('LAST VIRGIN', 'Similar to Lacoste White. Clean, crisp, and sophisticated.', 449, 45, 'last-virgin.png'),
('CHAMPAGNE BLUE', 'Similar to Bleu de Chanel. A bold, seductive scent.', 449, 40, 'champagne-blue.png'),
('CRAVE CONTROL', 'Similar to Creed Aventus. A powerful blend.', 449, 35, 'crave-control.png'),
('BURNS SO GOOD', 'Similar to Bvlgari Man Extreme.', 449, 30, 'burns-so-good.png'),
('CALL ME LATER', 'A sophisticated scent with aromatic notes.', 449, 40, 'call-me-later.png'),
('CALL ME NOW', 'An intense, captivating fragrance.', 449, 40, 'call-me-now.png'),
('JEALOUS TYPE', 'Similar to Jean Paul Gaultier Le Male.', 449, 50, 'jealous-type.png'),
('DIVINE SIN', 'Similar to Dior Sauvage.', 449, 50, 'divine-sin.png'),
('VERY NAUGHTY', 'Similar to Versace Eros.', 449, 50, 'very-naughty.png'),
('YOU SHOULD', 'Similar to Yves Saint Laurent Y.', 449, 50, 'you-should.png'),
('AREA SIXTY-NINE', 'Similar to Ariana Grande Cloud.', 449, 50, 'area-sixty-nine.png'),
('KARAT KISSES', 'Similar to Katy Perry Meow.', 449, 45, 'karat-kisses.png'),
('LACE ME UP', 'Similar to Lanvin Éclat d''Arpège.', 449, 40, 'lace-me-up.png'),
('VICIOUS BOMB', 'Similar to Victoria''s Secret Bombshell.', 449, 50, 'vicious-bomb.png'),
('VICIOUS EXTRACT', 'Similar to Victoria''s Secret Vanilla Lace.', 449, 45, 'vicious-extract.png'),
('BREAK THE ICE', 'Similar to Britney Spears Fantasy.', 449, 40, 'break-the-ice.png'),
('YOU WOULD HAVE', 'Similar to Yves Saint Laurent Libre.', 449, 50, 'you-would-have.png'),
('JOYFUL FEAR', 'Similar to Jo Malone English Pear & Freesia.', 449, 35, 'joyful-fear.png'),
('LAST TOUCH', 'Similar to Lacoste Touch of Pink.', 449, 40, 'last-touch.png'),
('PART-TIME ANGEL', 'Similar to Parfums de Marly Valaya.', 449, 30, 'part-time-angel.png'),
('BURN FOR YOU', 'Similar to Bvlgari Omnia Amethyste.', 449, 40, 'burn-for-you.png'),
('LEGALLY HIGH', 'Similar to Le Labo Santal 33.', 449, 50, 'legally-high.png'),
('BAD HABIT', 'Similar to Maison Francis Kurkdjian Baccarat Rouge 540.', 449, 45, 'bad-habit.png')
ON CONFLICT (name) DO NOTHING;