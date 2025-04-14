from app import create_app, db, bcrypt
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.notification import NotificationCategory, NotificationSettings, Notification, NotificationStatus
import os
from PIL import Image
import shutil

app = create_app()

with app.app_context():
    # Drop all tables and recreate them with the updated schema
    db.drop_all()
    db.create_all()
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin',
        is_approved=True,
        bio='System administrator',
        first_name='Admin',
        last_name='User'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create some sample posts
    post1 = Post(
        title='Welcome to our Blog',
        content='''<h2>Welcome to our Blog!</h2>
        <p>This is a sample post created by the admin. <strong>You can create your own posts</strong> after registering and logging in.</p>
        <p>The blog now supports <em>rich text formatting</em> with Quill editor, including:</p>
        <ul>
            <li>Bold and italic text</li>
            <li>Headings</li>
            <li>Lists</li>
            <li>Images (see below)</li>
            <li>Links</li>
        </ul>
        <p>Here's an example image:</p>
        <p><img src="https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600&amp;q=80" alt="Workspace with laptop"></p>
        <p>Happy blogging!</p>''',
        user_id=1,
        last_modified_by_id=1,  # Initially modified by admin (self)
        is_hidden=False
    )
    db.session.add(post1)
    
    # Create regular user
    user = User(
        username='user',
        email='user@example.com',
        role='user',
        is_approved=True,
        bio='Regular user account',
        first_name='Regular',
        last_name='User'
    )
    user.set_password('user123')
    db.session.add(user)
    
    # Commit to get IDs
    db.session.commit()
    
    # Create a post by regular user, modified by admin
    post2 = Post(
        title='My First Post',
        content='''<p>This is a post created by a regular user, but later edited by an admin to demonstrate the "Last modified by admin" feature.</p>
        <blockquote>The content has been enhanced with rich formatting to show how Quill editor works.</blockquote>
        <p>I can create:</p>
        <ol>
            <li>Numbered lists</li>
            <li>With multiple items</li>
        </ol>
        <p>And add <a href="https://example.com">links</a> too!</p>
        <p>Here's an image of nature:</p>
        <p><img src="https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=600&amp;q=80" alt="Beautiful landscape"></p>
        <p>You can also add captions under images like this one.</p>''',
        user_id=2,  # Created by regular user
        last_modified_by_id=1,  # Modified by admin
        is_hidden=False
    )
    db.session.add(post2)
    
    # Create a post with multiple images
    post3 = Post(
        title='Using Images in Your Posts',
        content='''<h2>How to Add Images to Your Posts</h2>
        <p>The Quill editor makes it easy to add images to your blog posts. Here's how:</p>
        <ol>
            <li>Click the image icon in the toolbar</li>
            <li>Enter the URL of your image</li>
            <li>The image will be inserted at your cursor position</li>
        </ol>
        <p>Here are some example images:</p>
        <p><img src="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600&amp;q=80" alt="Person typing on laptop"></p>
        <p>You can add multiple images to a post:</p>
        <p><img src="https://images.unsplash.com/photo-1516382799247-87df95d790b7?w=600&amp;q=80" alt="Coffee and computer"></p>
        <p>Images help make your posts more engaging and visually appealing!</p>''',
        user_id=1,  # Created by admin
        last_modified_by_id=1,  # Also modified by admin
        is_hidden=True  # This post is hidden as an example
    )
    db.session.add(post3)
    
    # Create a post with syntax highlighted code examples
    post_with_code = Post(
        title='Using Code Syntax Highlighting',
        content='''<p>This post demonstrates how to use syntax highlighting for code blocks in your posts!</p>
        <p>Here is an example of JavaScript code:</p>
        <pre class="ql-syntax" spellcheck="false">// JavaScript example
function greet(name) {
    console.log(`Hello, ${name}!`);
    return `Hello, ${name}!`;
}

// Call the function
greet('World');
</pre>
        <p>And here's some Python code:</p>
        <pre class="ql-syntax" spellcheck="false">def fibonacci(n):
    """Return the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Print first 10 Fibonacci numbers
for i in range(10):
    print(fibonacci(i))
</pre>
        <p>You can also use SQL:</p>
        <pre class="ql-syntax" spellcheck="false">SELECT users.name, COUNT(posts.id) as post_count
FROM users
LEFT JOIN posts ON users.id = posts.user_id
GROUP BY users.id
HAVING COUNT(posts.id) > 5
ORDER BY post_count DESC;
</pre>
        <p>Syntax highlighting makes your code more readable and easier to understand!</p>''',
        user_id=1,  # Created by admin
        is_hidden=False
    )
    db.session.add(post_with_code)
    
    # Create a helpful guide post for using syntax highlighting
    syntax_guide_post = Post(
        title='How to Use Code Syntax Highlighting',
        content='''<p>Our blog now supports syntax highlighting for code blocks! This makes sharing code in your posts much more readable and professional.</p>
        
        <h3>How to Add Code with Syntax Highlighting:</h3>
        <ol>
            <li>Click on the code block button (<code>&lt;/&gt;</code>) in the editor toolbar</li>
            <li>Paste or type your code in the code block</li>
            <li>The syntax will be automatically detected and highlighted</li>
        </ol>
        
        <h3>Supported Languages:</h3>
        <p>The syntax highlighter supports many popular languages including:</p>
        <ul>
            <li>JavaScript, TypeScript</li>
            <li>Python, Ruby, PHP</li>
            <li>HTML, CSS, XML</li>
            <li>C, C++, C#, Java</li>
            <li>SQL</li>
            <li>Bash, PowerShell</li>
            <li>JSON, YAML</li>
            <li>...and <a href="https://github.com/highlightjs/highlight.js/blob/main/SUPPORTED_LANGUAGES.md" target="_blank">many more!</a></li>
        </ul>
        
        <h3>Example Code Block:</h3>
        <pre class="ql-syntax" spellcheck="false">// This is a JavaScript example
function calculateSum(a, b) {
    return a + b;
}

// Use the function
const result = calculateSum(10, 20);
console.log(`The sum is ${result}`);
</pre>

        <h3>Tips for Better Code Blocks:</h3>
        <ul>
            <li>Keep code snippets concise and focused on what you're trying to demonstrate</li>
            <li>Include comments in your code to explain important concepts</li>
            <li>Use proper indentation for readability</li>
            <li>Test your code before posting if possible</li>
        </ul>
        
        <p>Happy coding!</p>''',
        user_id=1,  # Created by admin
        is_hidden=False
    )
    db.session.add(syntax_guide_post)
    
    db.session.commit()
    
    # Add sample comments
    comment1 = Comment(
        content='This is a great post! Thanks for sharing.',
        post_id=1,
        user_id=2  # user
    )
    
    comment2 = Comment(
        content='''<p>Welcome to our blog! I hope you enjoy your stay.</p>
        <p>Here's a helpful image for new bloggers:</p>
        <p><img src="https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=400&amp;q=80" alt="Person writing in a notebook"></p>''',
        post_id=1,
        user_id=1  # admin
    )
    
    comment3 = Comment(
        content='I notice this post was edited by an admin. Thanks for the improvements!',
        post_id=2,
        user_id=2  # user commenting on their own post that was edited by admin
    )
    
    # Comments for image tutorial post
    comment4 = Comment(
        content='<p>These image examples are very helpful! Is there a limit to how many images we can add?</p>',
        post_id=3,
        user_id=2  # user
    )
    
    comment5 = Comment(
        content='''<p>Great tutorial on adding images to posts!</p>
        <p>I'd also recommend using descriptive alt text for all images for better accessibility.</p>''',
        post_id=3,
        user_id=2  # user
    )
    
    # Add all comments to session
    db.session.add_all([comment1, comment2, comment3, comment4, comment5])
    db.session.commit()
    
    # Add replies to comments
    reply1 = Comment(
        content='''<p>Thank you for your kind words!</p>
        <p>Here's a quick tip for writing great blog posts:</p>
        <p><img src="https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=300&amp;q=80" alt="Writing ideas"></p>''',
        post_id=1,
        user_id=1,  # admin
        parent_id=1  # reply to comment1
    )
    
    reply2 = Comment(
        content='''<p>There's no hard limit on the number of images, but keeping posts focused with 3-5 relevant images is a good practice.</p>
        <p>Here's an example of image sizing:</p>
        <p><img src="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=300&amp;q=80" alt="Computer with code"></p>''',
        post_id=3,
        user_id=1,  # admin
        parent_id=4  # reply to comment4
    )
    
    # Add all replies
    db.session.add_all([reply1, reply2])
    db.session.commit()
    
    # Create default notification categories
    categories = [
        NotificationCategory(name="Comments", description="Notifications about comments on your posts", icon="fa-comment"),
        NotificationCategory(name="Replies", description="Notifications about replies to your comments", icon="fa-reply"),
        NotificationCategory(name="Mentions", description="Notifications when someone mentions you", icon="fa-at"),
        NotificationCategory(name="System", description="System notifications and announcements", icon="fa-bell")
    ]
    for category in categories:
        db.session.add(category)
    
    db.session.commit()
    
    # Create notification settings for users
    NotificationSettings.create_default_settings(admin)
    NotificationSettings.create_default_settings(user)
    
    # Create sample notifications
    notification1 = Notification(
        user_id=2,  # for regular user
        category_id=1,  # Comments category
        sender_id=1,  # from admin
        post_id=1,
        comment_id=2,
        notification_type=Notification.TYPE_COMMENT,
        title="New Comment on Your Post",
        message="Admin commented on your post: Welcome to our blog! I hope you enjoy your stay.",
        link="/post/1#comment-2",
        status=NotificationStatus.UNREAD
    )
    
    notification2 = Notification(
        user_id=2,  # for regular user
        category_id=4,  # System category
        notification_type=Notification.TYPE_SYSTEM,
        title="Welcome to the Blog!",
        message="Thank you for joining our community. We hope you enjoy your experience here.",
        status=NotificationStatus.UNREAD
    )
    
    notification3 = Notification(
        user_id=1,  # for admin
        category_id=2,  # Replies category
        sender_id=2,  # from user
        post_id=1,
        comment_id=1,
        notification_type=Notification.TYPE_REPLY,
        title="New Reply to Your Comment",
        message="User replied to your comment: This is a great post! Thanks for sharing.",
        link="/post/1#comment-1",
        status=NotificationStatus.READ
    )
    
    db.session.add_all([notification1, notification2, notification3])
    db.session.commit()
    
    print('Database initialized with admin user, sample data, comments, and notifications.')

    # Create profile pictures directory if it doesn't exist
    profile_pics_dir = os.path.join(app.root_path, 'static/profile_pics')
    os.makedirs(profile_pics_dir, exist_ok=True)
    
    # Create default profile picture
    default_pic = os.path.join(profile_pics_dir, 'default.jpg')
    if not os.path.exists(default_pic):
        # Create a simple default profile picture
        img = Image.new('RGB', (150, 150), color = (73, 109, 137))
        img.save(default_pic)
        print('Created default profile picture.')
    
    print('Database setup complete!') 