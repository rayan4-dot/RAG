import { useState } from 'react';
import { Layout } from './components/Layout';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';

function App() {
  const [isDocumentReady, setIsDocumentReady] = useState(false);

  const handleUploadSuccess = () => {
    setIsDocumentReady(true);
  };

  return (
    <Layout>
      {!isDocumentReady ? (
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      ) : (
        <ChatInterface />
      )}
    </Layout>
  );
}

export default App;
