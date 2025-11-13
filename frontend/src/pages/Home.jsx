import { json } from "d3";
import { useState, useEffect } from "react"

const Home = () => {
    const [userText, setUserText] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [status, setStatus] = useState('');
    const [data, setData] = useState(null)

    const handleSubmit = async (e) => {
         e.preventDefault(); // Prevent page reload

    if (!userText.trim()) {
      setStatus('Please enter some text.');
      return;
    }

    setIsSending(true);
    setStatus('');

    try {
      const response = await fetch('http://localhost:8000/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          "repo_root": userText // ✅ Your text goes here in the body
        }),
      });

      if (response.ok) {
        setStatus('Sent successfully!');
        setUserText(''); // Clear after success (optional)
        setData(await response.json())
      } else {
        setStatus('Failed to send. Please try again.');
      }
      
    } catch (error) {
      console.error('Error:', error);
      setStatus('Network error. Check your connection.');
    } finally {
      setIsSending(false);
    }
  };
    return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="userInput">Enter project local path:</label>
        <br />
        <textarea
          id="userInput"
          value={userText}
          onChange={(e) => setUserText(e.target.value)}
          rows={5}
          cols={50}
          placeholder="Type project path here..."
          disabled={isSending}
        />
      </div>
      <br />
      <button type="submit" disabled={isSending || !userText.trim()}>
        {isSending ? 'Sending...' : 'Send to Service'}
      </button>
      {status && <p>{status}</p>}
        {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </form>
  );
}

export default Home