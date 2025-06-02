// Productos de ejemplo
const products = [
    {
        id: 1,
        title: "Auriculares RGB Pro",
        price: 89,
        img: "https://placehold.co/140x140/00ffe7/181c2f?text=Headset"
    },
    {
        id: 2,
        title: "Teclado Mecánico Neon",
        price: 120,
        img: "https://placehold.co/140x140/ff00c8/181c2f?text=Keyboard"
    },
    {
        id: 3,
        title: "Mouse Gamer X-Glide",
        price: 59,
        img: "https://placehold.co/140x140/23264a/00ffe7?text=Mouse"
    },
    {
        id: 4,
        title: "Controlador Inalámbrico",
        price: 75,
        img: "https://placehold.co/140x140/ff00c8/23264a?text=Controller"
    },
    {
        id: 5,
        title: "Silla Gaming LED",
        price: 299,
        img: "https://placehold.co/140x140/00ffe7/ff00c8?text=Chair"
    },
    {
        id: 6,
        title: "Monitor 4K UltraWide",
        price: 499,
        img: "https://placehold.co/140x140/23264a/ff00c8?text=Monitor"
    }
];

// Renderizar productos
const productsContainer = document.getElementById('products');
products.forEach(product => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
        <img src="${product.img}" alt="${product.title}">
        <div class="product-title">${product.title}</div>
        <div class="product-price">$${product.price}</div>
        <button class="add-cart-btn" data-id="${product.id}">Agregar al carrito</button>
    `;
    productsContainer.appendChild(card);
});

// Carrito
let cart = [];

function renderCart() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    cartItems.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.title} x${item.qty}</span>
            <span>$${item.price * item.qty}</span>
        `;
        cartItems.appendChild(li);
        total += item.price * item.qty;
    });
    
    cartTotal.textContent = `Total: $${total}`;
}

// Agregar al carrito
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('add-cart-btn')) {
        const id = parseInt(e.target.getAttribute('data-id'));
        const product = products.find(p => p.id === id);
        const cartItem = cart.find(item => item.id === id);
        
        if (cartItem) {
            cartItem.qty += 1;
        } else {
            cart.push({ ...product, qty: 1 });
        }
        
        renderCart();

        // Efecto visual de confirmación
        e.target.textContent = '¡Agregado!';
        e.target.style.background = 'linear-gradient(90deg, var(--accent2), var(--accent))';
        setTimeout(() => {
            e.target.textContent = 'Agregar al carrito';
            e.target.style.background = '';
        }, 1000);
    }
});

// Inicializar carrito
renderCart();

// Hacer que los elementos del menú sean clickeables
document.querySelectorAll('nav li').forEach(item => {
    item.addEventListener('click', function() {
        // Aquí puedes agregar la navegación a las diferentes secciones
        alert('Navegando a: ' + this.textContent);
    });
});