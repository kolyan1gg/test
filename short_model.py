#pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
import json
from file_downl_try import get_vit_file

def get_categories_vit(new_image_path):

    import torch
    from torchvision import transforms
    import torch.nn as nn
    import pandas as pd


    # Определение трансформаций 
    transform_norm_new = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5018, 0.4925, 0.4460], # Наши подсчитанные значения mean и std для нормализации
                            std=[0.2339, 0.2276, 0.2402])
    ])

      

    import timm


    # Load pre-trained VIT model
    model = timm.create_model('vit_base_patch32_clip_224.openai_ft_in1k', pretrained=True) # to check others models as well

    # Check if GPU is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    model = model.to(device)

    num_classes = 81 #no_of_classes
    model.head = nn.Linear(model.head.in_features, num_classes, device = device)

    # Then load the state dictionary
    get_vit_file() # download file if not exists
    model.load_state_dict(torch.load('vit_base_patch32_state_dict.pth', map_location=device))

   
    # Test the model on one image

    from torchvision import transforms
    from PIL import Image

    # Load image
    #image_path = 'extra images test/shiba-inu.webp' # test image path
    image_path = new_image_path # test image path
    image = Image.open(image_path)

    # Transform the image
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to the size that model expects
        transforms.ToTensor(),  # Convert to tensor
        transforms.Normalize(mean=[0.5018, 0.4925, 0.4460], std=[0.2339, 0.2276, 0.2402]),  # Normalize
    ])

    image = transform(image).unsqueeze(0)  # Add a batch dimension

    import torch
    import pandas as pd
    import torch.nn.functional as F

    with torch.no_grad():  # Disable gradient tracking
        image = image.to('cuda' if torch.cuda.is_available() else 'cpu')
        outputs = model(image)
        probabilities = F.softmax(outputs, dim=1)

    # Get top categories
    top_num = 5  # Number of top categories you want
    top_prob, top_catid = torch.topk(probabilities, top_num)

    # Load category names
    with open('class_to_idx.json', 'r') as f:
        class_to_idx = json.load(f)

    # Get class names for prediction index
    idx_to_class = {v: k for k, v in class_to_idx.items()}


    # Convert to Python data types and print
    top_prob = top_prob.cpu().numpy()[0]
    top_catid = top_catid.cpu().numpy()[0]

    predictions = []
    for i in range(top_num):
        predicted_class_name = idx_to_class[top_catid[i]]
        predicted_probability = top_prob[i]
        predictions.append({'Category ID': predicted_class_name, 'Probability': predicted_probability})

    df = pd.DataFrame(predictions)
    df_string = df.to_string(index=False)
    print(df_string)

    return df_string

def get_categories_rn(new_image_path):
    import torch
    from torchvision import transforms
    from PIL import Image
    import pandas as pd
    import torchvision.models as models
    import torch.nn as nn

    # Load image
    image_path = new_image_path # test image path
    image = Image.open(image_path)

    # Load image
    #image_path = 'extra images test/horse.jpg' # test image path
    #image = Image.open(image_path)  


    # Transform the image
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to the size your model expects
        transforms.ToTensor(),  # Convert to tensor
        transforms.Normalize(mean=[0.5018, 0.4925, 0.4460], std=[0.2339, 0.2276, 0.2402]),  # Normalize
    ])

    image = transform(image).unsqueeze(0)  # Add a batch dimension

    # Load category names
    with open('class_to_idx.json', 'r') as f:
        class_to_idx = json.load(f)

    # First, recreate the model architecture
    resnet = models.resnet50(weights=True)

    # Check if GPU is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    resnet = resnet.to(device)

    #num_classes = len(class_to_idx)
    num_classes = 81
    resnet.fc = nn.Linear(resnet.fc.in_features, num_classes, device = device)

    # Then load the state dictionary
    resnet.load_state_dict(torch.load('resnet50_state_dict.pth', map_location=device))


    # Move model to GPU
    resnet = resnet.to('cuda' if torch.cuda.is_available() else 'cpu')
    #resnet.eval()

    import torch
    import torch.nn.functional as F

    with torch.no_grad():  # Disable gradient tracking
        image = image.to('cuda' if torch.cuda.is_available() else 'cpu')
        outputs = resnet(image)
        probabilities = F.softmax(outputs, dim=1)

    # Get top categories
    top_num = 5  # Number of top categories you want
    top_prob, top_catid = torch.topk(probabilities, top_num)

    
    # Get class names for prediction index
    idx_to_class = {v: k for k, v in class_to_idx.items()}

    # Convert to Python data types and print
    top_prob = top_prob.cpu().numpy()[0]
    top_catid = top_catid.cpu().numpy()[0]

    predictions = []
    for i in range(top_num):
        predicted_class_name = idx_to_class[top_catid[i]]
        predicted_probability = top_prob[i]
        predictions.append({'Category ID': predicted_class_name, 'Probability': predicted_probability})

    df = pd.DataFrame(predictions)
    df_string = df.to_string(index=False)
    print(df_string)

    return df_string