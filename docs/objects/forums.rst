Forums
------

ForumCategory
^^^^^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "name": "Site",
    "description": "Stuff about the site",
    "position": 1,
    "deleted": false
  }

* **id** - The forum category's ID
* **name** - The forum category's name
* **description** - A description of the subforums in the category
* **position** - Position of the category compared to other categories
* **deleted** - Whether or not the category is deleted

Forum
^^^^^

.. parsed-literal::
  {
    "id": 1,
    "name": "Pulsar",
    "description": "Talk about the codebase",
    "category": "<ForumCategory>",
    "position": 1,
    "thread_count": 2,
    "threads": [
      "<ForumThread>",
      "<ForumThread>"
    ],
    "deleted": false,
    "last_updated_thread": "<ForumThread>"
  }

* **id** - The forum's ID
* **name** - The forum's name
* **description** - A description of the forum
* **category** - The category that this forum belongs to.
* **position** - Position of the forum compared to other forums
* **thread_count** - The number of threads in the forum
* **threads** - Forum threads in the forum
* **deleted** - Whether or not the forum is deleted
* **last_updated_thread** - The most recently updated thread in the forum

ForumThread
^^^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "topic": "Welcome to our new site",
    "forum": "<Forum>",
    "poster": "<User>",
    "locked": false,
    "sticky": false,
    "created_time": 1514764800,
    "poll": "<ForumPoll>",
    "last_post": "<ForumPost>",
    "last_viewed_post": "<ForumPost>",
    "subscribed": true,
    "post_count": 231,
    "posts": [
      "<ForumPost>",
      "<ForumPost>"
    ],
    "thread_notes": [
      "<ForumThreadNote>",
      "<ForumThreadNote>"
    ],
    "deleted": false
  }

* **id** - The forum thread's ID
* **topic** - The thread's topic/title
* **forum** - The forum that the thread was posted in
* **poster** - The user who created the thread
* **locked** - Whether or not the thread is locked
* **sticky** - Whether or not the forum thread is stickied
* **created_time** - When the thread was created
* **poll** - The poll attached to the forum thread (if present)
* **last_post** - The most recent forum post in the thread
* **last_viewed_post** - The last forum post in the thread viewed by the user
* **subscribed** - Whether or not requesting user is subscribed to the thread
* **post_count** - The number of forum posts in the thread
* **posts** - Forum posts in the thread
* **thread_notes** - The staff notes corresponding to the forum thread
* **deleted** - Whether or not the thread is deleted

ForumPost
^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "thread": "<ForumThread>",
    "poster": "<User>",
    "contents": "I like beans.",
    "time": 1514768800,
    "edited_time": 1514768900,
    "sticky": false,
    "editor": "<User>",
    "deleted": false,
    "edit_history": [
      "<ForumPostEditHistory>",
      "<ForumPostEditHistory>"
    ]
  }

* **id** - The forum post's ID
* **thread** - The forum thread the post was made in
* **poster** - The user who made the post
* **contents** - The text contents of the post
* **time** - When the post was made
* **edited_time** - The most recent time the forum post was edited
* **sticky** - Whether or not the post is stickied
* **editor** - The most recent user to edit the post
* **deleted** - Whether or not the post is deleted
* **edit_history** - The edit history of the forum post

ForumPostEditHistory
^^^^^^^^^^^^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "editor": "<User>",
    "contents": "I like benas.",
    "time": 1514768800
  }

* **id** - The forum post's ID
* **editor** - The user who edited the post to the returned contents
* **contents** - The contents of the post after the edit
* **time** - The time of the edit

ForumThreadNote
^^^^^^^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "note": "This thread sucks.",
    "user": "<User>",
    "time": 1514769800
  }

* **id** - The forum thread's ID
* **note** - The text contents of the thread note
* **user** - The user who created the thread note
* **time** - When the note was added

ForumPoll
^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "thread": "<ForumThread>",
    "question": "Do you like beans?",
    "closed": false,
    "featured": false,
    "choices": [
      "<ForumPollChoice>",
      "<ForumPollChoice>"
    ]
  }

* **id** - The forum poll's ID
* **thread** - The forum thread that the poll is associated with
* **question** - The poll's question
* **closed** - Whether or not the poll is closed
* **featured** - Whether or not the poll is featured on the site
* **choices** - The answer choices for the poll

ForumPollChoice
^^^^^^^^^^^^^^^

.. parsed-literal::
  {
    "id": 1,
    "choice": "Yes!",
    "answers": 102
  }

* **id** - The ID of the answer choice
* **choice** - The text of the answer choice
* **answers** - The number of users who selected this choice* **choice** - The text
  of the answer choice
